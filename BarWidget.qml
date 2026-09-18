import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// Root is Ui/Panel: the PanelController that drives KeyboardPanel lives
// there, not in Ui/BarWidget.
Panel {
  id: root
  moduleName: "io.github.pietjepuh.earth"
  ipcTarget: "io.github.pietjepuh.earth"

  // Manual settings always win over IP auto-detect: an explicit value the
  // user typed in must never be silently overridden by a background lookup.
  readonly property real manualLat: Number(root.setting("lat", NaN))
  readonly property real manualLon: Number(root.setting("lon", NaN))
  property real autoLat: NaN
  property real autoLon: NaN
  property string autoCity: ""
  property bool locating: false
  property string locateError: ""

  readonly property real lat: !isNaN(manualLat) ? manualLat : autoLat
  readonly property real lon: !isNaN(manualLon) ? manualLon : autoLon
  readonly property bool usingAutoLocation: isNaN(manualLat) && !isNaN(autoLat)

  readonly property string locationCachePath:
    Quickshell.env("HOME") + "/.cache/omarchy-earth/location.json"

  readonly property real span: Number(root.setting("span", 4.0))
  readonly property int radiusNm: Number(root.setting("radiusNm", 50))
  readonly property int intervalSec: Number(root.setting("intervalSec", 300))
  readonly property bool showLabel: root.setting("showLabel", true)
  readonly property bool configured: !isNaN(lat) && !isNaN(lon)

  // Derived muted color
  readonly property color mutedColor: root.bar && root.bar.foreground
    ? Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.55)
    : "#707880"

  property string currentTab: "weer"

  // Live state from sampler
  property string summary: "…"
  property var weather: ({})
  property var nowcast: ({})
  property var advice: []
  property var hoveredAdvice: null
  property var solar: ({})
  property var aircraft: []
  property int planeCount: 0
  property var emergencies: []
  property int hoveredPlane: -1
  property var air: ({})
  property var pollen: ({})
  property var metar: ({})
  property var metarCounts: ({})
  property var quakes: []
  property var disasters: []
  property var militaryAircraft: []
  property int militaryCount: 0
  property var militaryNearby: []
  property var waterways: []
  property var nuclear: []
  property var militaryBases: []
  property var hotspots: []
  property var news: []
  property var spaceWeather: ({})
  property var submarineCables: []
  property var pipelines: []
  property var datacenters: []
  property var vessels: ({})
  property var droneStatus: ({})
  property var droneZones: []
  property var trains: []
  property var webcams: []
  property int radarFrames: 0
  property string lastError: ""
  property bool busy: false
  property bool destroying: false

  readonly property string pluginDir:
    Quickshell.env("HOME") + "/.config/omarchy/plugins/io.github.pietjepuh.earth"
  readonly property string mapPath:
    Quickshell.env("HOME") + "/.cache/omarchy-earth/earth.html"

  visible: configured
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function refresh() {
    if (!configured || destroying || sampler.running) return
    busy = true
    sampler.running = true
  }

  function openMap() {
    if (!configured || builder.running || focusCheck.running) return
    busy = true
    // Reusing an existing window avoids piling up chromium instances every
    // time someone clicks "Open Map" -- each one is a full process tree
    // (zygote, gpu, renderer, utility), and a stale one left on an
    // unrelated page (e.g. someone navigated to Google Earth inside it)
    // looked like the plugin was stuck, because the click did nothing
    // visible: a new window never opened, and the old one was not the one
    // in focus.
    focusCheck.running = true
  }

  // jq is already a dependency of nothing here, so this is done in python3
  // (already required by sampler/builder) rather than adding jq as a new
  // one. Matches on window title, not class: Chromium's --app mode
  // ignores --class and derives its own appid from the file:// URL's path
  // (e.g. "chrome-__home_tim_.cache_omarchy-earth_earth.html-Default"),
  // which embeds the user's home directory and is not something a plugin
  // can predict. The page's own <title> is stable across machines.
  Process {
    id: focusCheck
    running: false
    command: ["python3", "-c",
      "import json,subprocess,sys\n" +
      "out = subprocess.run(['hyprctl','clients','-j'], capture_output=True, text=True).stdout\n" +
      "try:\n" +
      "    clients = json.loads(out)\n" +
      "except Exception:\n" +
      "    clients = []\n" +
      "hit = any(c.get('title') == 'Earth & Intel Wereldkaart' for c in clients)\n" +
      "print('found' if hit else 'missing')\n"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        if (root.destroying) return
        if (text.trim() === "found") {
          root.bar.run("hyprctl dispatch " + "'hl.dsp.focus({ window = \"title:Earth & Intel Wereldkaart\" })'")
          root.busy = false
        } else {
          builder.running = true
        }
      }
    }
    onExited: function(code) {
      if (code !== 0 && !root.destroying) {
        // Could not even check -- fall back to the old behaviour rather
        // than leaving the click silently doing nothing.
        builder.running = true
      }
    }
  }

  // Auto-location: IP-based, since a desktop has no GPS. Only runs when no
  // manual lat/lon is set. Cached to disk so a restart does not repeat the
  // network call on every shell reload -- the gap that made the equivalent
  // lookup in another plugin re-fire every time.
  function locateByIp() {
    if (!isNaN(manualLat) || locating || destroying) return
    locating = true
    locateError = ""
    locator.running = true
  }

  function loadCachedLocation() {
    cacheReader.running = true
  }

  Process {
    id: cacheReader
    running: false
    command: ["cat", root.locationCachePath]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        if (root.destroying || text.trim() === "") {
          root.locateByIp()
          return
        }
        try {
          var c = JSON.parse(text)
          var age = Date.now() / 1000 - (c.ts || 0)
          // Refresh every 6 hours -- an IP-based city rarely moves faster
          // than that, and it keeps this off the network on every restart.
          if (c.lat !== undefined && age < 6 * 3600) {
            root.autoLat = c.lat
            root.autoLon = c.lon
            root.autoCity = c.city || ""
            return
          }
        } catch (e) { /* fall through to a fresh lookup */ }
        root.locateByIp()
      }
    }
    onExited: function(code) {
      // cat on a missing file exits non-zero; stdout is simply empty then,
      // and onStreamFinished above already triggers a fresh lookup.
    }
  }

  Process {
    id: locator
    running: false
    // ipwho.is answers over HTTPS with no key; verified more accurate for
    // this region than ip-api.com (HTTP only) or ipapi.co (was off by a
    // whole city). Sent once per cache expiry, not per poll.
    command: ["curl", "-sS", "--max-time", "10", "https://ipwho.is/"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        root.locating = false
        if (root.destroying) return
        var loc
        try {
          loc = JSON.parse(text)
        } catch (e) {
          root.locateError = "locatie ophalen mislukt"
          return
        }
        if (!loc.success || typeof loc.latitude !== "number") {
          root.locateError = "locatie ophalen mislukt"
          return
        }
        root.autoLat = loc.latitude
        root.autoLon = loc.longitude
        root.autoCity = [loc.city, loc.country].filter(function(s) { return !!s }).join(", ")
        root.writeLocationCache()
      }
    }
    onExited: function(code) {
      if (code !== 0 && !root.destroying && isNaN(root.autoLat))
        root.locateError = "geen netwerk voor locatie"
    }
  }

  Process {
    id: cacheWriter
    running: false
    // python3 is already a dependency (sampler/builder use it); writing via
    // argv avoids the shell-quoting a nested sh -c string would need for a
    // path and a JSON payload together.
    command: []
    onRunningChanged: {}
  }

  function writeLocationCache() {
    var payload = JSON.stringify({
      lat: root.autoLat, lon: root.autoLon, city: root.autoCity,
      ts: Math.floor(Date.now() / 1000)
    })
    cacheWriter.command = ["python3", "-c",
      "import sys, os\n" +
      "p = sys.argv[1]\n" +
      "os.makedirs(os.path.dirname(p), exist_ok=True)\n" +
      "open(p, 'w').write(sys.argv[2])\n",
      root.locationCachePath, payload]
    cacheWriter.running = true
  }

  Component.onCompleted: {
    if (isNaN(manualLat)) loadCachedLocation()
  }

  Process {
    id: sampler
    running: false
    command: ["python3", root.pluginDir + "/bin/earth-sampler.py",
              "--lat", String(root.lat), "--lon", String(root.lon),
              "--span", String(root.span),
              "--radius", String(root.radiusNm),
              "--once"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        root.busy = false
        if (root.destroying) return
        var obj
        try {
          obj = JSON.parse(text)
        } catch (e) {
          root.lastError = "kon data niet lezen"
          return
        }
        root.summary          = String(obj.summary || "…")
        root.weather          = obj.weather || ({})
        root.nowcast          = obj.nowcast || ({})
        root.advice           = obj.advice || []
        root.solar            = obj.solar || ({})
        root.aircraft         = (obj.aircraft && obj.aircraft.items) || []
        root.planeCount       = (obj.aircraft && obj.aircraft.count) || 0
        root.emergencies      = (obj.aircraft && obj.aircraft.emergencies) || []
        root.militaryAircraft = (obj.military_aircraft && obj.military_aircraft.items) || []
        root.militaryCount    = (obj.military_aircraft && obj.military_aircraft.count) || 0
        root.militaryNearby   = (obj.military_aircraft && obj.military_aircraft.nearby) || []
        root.waterways        = obj.waterways || []
        root.nuclear          = obj.nuclear || []
        root.militaryBases    = obj.military_bases || []
        root.hotspots         = obj.hotspots || []
        root.news             = obj.news || []
        root.spaceWeather     = obj.space_weather || ({})
        root.submarineCables  = obj.submarine_cables || []
        root.pipelines        = obj.pipelines || []
        root.datacenters      = obj.datacenters || []
        root.vessels          = obj.vessels || ({})
        root.droneStatus      = obj.drone_status || ({})
        root.droneZones       = obj.drone_zones || []
        root.trains           = obj.trains || []
        root.webcams          = obj.webcams || []
        root.air              = obj.air || ({})
        root.pollen           = obj.pollen || ({})
        root.metar            = obj.metar || ({})
        root.metarCounts      = (obj.metar && obj.metar.counts) || ({})
        root.quakes           = (obj.quakes && obj.quakes.events) || []
        root.disasters        = (obj.disasters && obj.disasters.events) || []
        root.radarFrames      = (obj.radar && obj.radar.frames) ? obj.radar.frames.length : 0
        root.lastError        = ""
      }
    }
    onExited: function(code) {
      root.busy = false
      if (code !== 0 && !root.destroying) root.lastError = "sampler stopte met " + code
    }
  }

  Process {
    id: builder
    running: false
    command: ["python3", root.pluginDir + "/bin/build-map.py",
              "--lat", String(root.lat), "--lon", String(root.lon),
              "--span", String(root.span), "--out", root.mapPath]
    onExited: function(code) {
      root.busy = false
      if (root.destroying) return
      if (code === 0) {
        root.bar.run("chromium --app=file://" + root.mapPath
          + " --class=omarchy-earth"
          + " --user-data-dir=" + Quickshell.env("HOME") + "/.cache/omarchy-earth/browser")
      } else {
        root.lastError = "kaart bouwen mislukte (" + code + ")"
      }
    }
  }

  Timer {
    interval: Math.max(60, root.intervalSec) * 1000
    running: root.configured && !root.destroying
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Component.onDestruction: {
    root.destroying = true
    sampler.running = false
    builder.running = false
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.showLabel ? ("\u{1F30D} " + root.summary) : "\u{1F30D}"
    fontSize: Style.font.caption
    horizontalMargin: 10
    active: (root.nowcast && root.nowcast.raining_now) || (root.emergencies && root.emergencies.length > 0)
    tooltipText: root.lastError !== "" ? root.lastError
      : (root.summary + " \u00b7 klik voor details, k voor kaart")
    onPressed: function() { root.toggle() }
  }

  KeyboardPanel {
    id: panel
    anchorItem: root
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(720)
    contentHeight: panel.fittedContentHeight(body.implicitHeight + 24)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTextKey: function(text) {
        if (text === "r") root.refresh()
        if (text === "k") root.openMap()
        if (text === "1") root.currentTab = "weer"
        if (text === "2") root.currentTab = "vluchten"
        if (text === "3") root.currentTab = "milieu"
      }

      ColumnLayout {
        id: body
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // Header
        RowLayout {
          Layout.fillWidth: true
          spacing: 8

          // Open Map Button. Placed first so it always keeps its own
          // width even under a tight fittedContentWidth() clamp -- with
          // the title column filling first, this button used to get
          // squeezed out of the visible panel entirely.
          Rectangle {
            implicitHeight: 32
            implicitWidth: mapBtnRow.implicitWidth + 16
            radius: 4
            color: mapHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.06)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.15)
            HoverHandler { id: mapHover }
            TapHandler { onTapped: root.openMap() }

            RowLayout {
              id: mapBtnRow
              anchors.centerIn: parent
              spacing: 6
              Text {
                text: root.busy ? "\u25CC" : "\u{1F5FA}"
                font.pixelSize: 13
                color: root.bar ? root.bar.foreground : "#ddd"
              }
              Text {
                text: root.busy ? "bezig\u2026" : "Kaart openen (k)"
                color: root.bar ? root.bar.foreground : "#ddd"
                font.family: root.bar ? root.bar.fontFamily : ""
                font.pixelSize: 11
                font.bold: true
              }
            }
          }

          ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 2
            Text {
              Layout.fillWidth: true
              text: "Earth \u00b7 Wereld & Weer"
              color: root.bar ? root.bar.foreground : "#fff"
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 15
              font.bold: true
              elide: Text.ElideRight
            }
            Text {
              Layout.fillWidth: true
              text: root.lastError !== "" ? root.lastError : root.summary
              color: root.lastError !== "" ? (root.bar ? root.bar.urgent : "#a55") : root.mutedColor
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 10
              elide: Text.ElideRight
              maximumLineCount: 2
              wrapMode: Text.WordWrap
            }
            Text {
              Layout.fillWidth: true
              visible: root.usingAutoLocation || root.locating || root.locateError !== ""
              text: root.locating ? "locatie bepalen via IP…"
                : root.locateError !== "" ? root.locateError
                : root.usingAutoLocation ? ("locatie via IP: " + (root.autoCity || "?") + "  ·  klik om te herladen")
                : ""
              color: root.mutedColor
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 9
              font.italic: true
              elide: Text.ElideRight
              maximumLineCount: 1
              wrapMode: Text.WordWrap

              TapHandler {
                enabled: root.usingAutoLocation
                onTapped: root.locateByIp()
              }
            }
          }
        }

        // Tabs
        RowLayout {
          Layout.fillWidth: true
          spacing: 6

          Repeater {
            model: [
              { key: "weer",     label: "\u2600 Weer & Advies" },
              { key: "vluchten", label: "\u2708 Vluchten & Radar" },
              { key: "milieu",   label: "\u{1F30D} Milieu & Wereld" }
            ]
            delegate: Rectangle {
              Layout.fillWidth: true
              implicitHeight: 26
              radius: 3
              color: root.currentTab === modelData.key
                ? (root.bar ? Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.15) : "#333")
                : "transparent"
              border.width: 1
              border.color: root.currentTab === modelData.key
                ? (root.bar ? root.bar.foreground : "#888")
                : Qt.rgba(1, 1, 1, 0.1)

              Text {
                anchors.centerIn: parent
                text: modelData.label
                color: root.currentTab === modelData.key
                  ? (root.bar ? root.bar.foreground : "#fff")
                  : root.mutedColor
                font.family: root.bar ? root.bar.fontFamily : ""
                font.pixelSize: 11
                font.bold: root.currentTab === modelData.key
              }

              MouseArea {
                anchors.fill: parent
                onClicked: {
                  root.currentTab = modelData.key
                  if (modelData.key === "vluchten") scopeCanvas.requestPaint()
                }
              }
            }
          }
        }

        Rectangle {
          Layout.fillWidth: true
          implicitHeight: 1
          color: Qt.rgba(1, 1, 1, 0.08)
        }

        // ====================================================================
        // TAB 1: WEER & ADVIES
        // ====================================================================
        ColumnLayout {
          Layout.fillWidth: true
          visible: root.currentTab === "weer"
          spacing: 8

          // Current conditions card
          RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
              text: (root.weather && root.weather.current && root.weather.current.temp != null)
                ? (root.weather.current.temp.toFixed(1) + "°C") : "--°C"
              color: root.bar ? root.bar.foreground : "#fff"
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 22
              font.bold: true
            }

            ColumnLayout {
              Layout.fillWidth: true
              spacing: 1
              Text {
                text: {
                  var cw = root.weather ? root.weather.current : null
                  if (!cw) return "Laden…"
                  var bits = [cw.description || ""]
                  if (cw.feels_like != null) bits.push("voelt als " + cw.feels_like.toFixed(0) + "°C")
                  return bits.join(" · ")
                }
                color: root.bar ? root.bar.foreground : "#ddd"
                font.family: root.bar ? root.bar.fontFamily : ""
                font.pixelSize: 11
                font.bold: true
              }
              Text {
                text: {
                  var cw = root.weather ? root.weather.current : null
                  if (!cw) return ""
                  var parts = []
                  if (cw.wind_speed_kmh != null) {
                    var w = "wind " + cw.wind_speed_kmh + " km/u (" + (cw.wind_bft || 0) + " Bft)"
                    if (cw.wind_gusts_kmh) w += " (vlaag " + cw.wind_gusts_kmh + ")"
                    parts.push(w)
                  }
                  if (cw.humidity != null) parts.push(cw.humidity + "% vocht")
                  if (cw.pressure_hpa != null) parts.push(cw.pressure_hpa + " hPa")
                  if (cw.dew_point != null) parts.push("dauw " + cw.dew_point + "°C")
                  if (cw.visibility_km != null) parts.push("zicht " + cw.visibility_km + " km")
                  if (cw.uv_index != null && cw.uv_index > 0) parts.push("UV " + cw.uv_index.toFixed(0))
                  return parts.join(" · ")
                }
                color: root.mutedColor
                font.family: root.bar ? root.bar.fontFamily : ""
                font.pixelSize: 10
                wrapMode: Text.WordWrap
              }
            }
          }

          // Practical activity verdicts
          Text {
            Layout.fillWidth: true
            Layout.topMargin: 2
            text: "Adviezen"
            color: root.bar ? root.bar.foreground : "#ddd"
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 11
            font.bold: true
          }

          Flow {
            Layout.fillWidth: true
            spacing: 5

            Repeater {
              model: root.advice
              delegate: Rectangle {
                radius: 3
                implicitWidth: chipText.implicitWidth + 14
                implicitHeight: 22
                color: modelData.verdict === "yes"
                  ? Qt.rgba(0.36, 0.72, 0.36, 0.22)
                  : modelData.verdict === "caution"
                    ? Qt.rgba(0.88, 0.70, 0.31, 0.22)
                    : Qt.rgba(1, 1, 1, 0.05)
                border.width: 1
                border.color: modelData.verdict === "yes"
                  ? "#5cb85c"
                  : modelData.verdict === "caution"
                    ? "#e0b34f"
                    : Qt.rgba(1, 1, 1, 0.12)

                Text {
                  id: chipText
                  anchors.centerIn: parent
                  text: (modelData.verdict === "yes" ? "\u2713 " : modelData.verdict === "caution" ? "~ " : "\u2717 ")
                        + modelData.label
                  color: modelData.verdict === "yes"
                    ? "#6ec96e"
                    : modelData.verdict === "caution"
                      ? "#f0c868"
                      : root.mutedColor
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                  font.bold: modelData.verdict === "yes"
                }

                HoverHandler {
                  onHoveredChanged: if (hovered) root.hoveredAdvice = modelData
                }
              }
            }
          }

          // Reason text following hover
          Text {
            Layout.fillWidth: true
            text: {
              var a = root.hoveredAdvice
              if (a && a.label) return a.label + " \u00b7 " + (a.reason || "")
              for (var i = 0; i < root.advice.length; i++) {
                if (root.advice[i].verdict === "yes")
                  return root.advice[i].label + " \u00b7 " + root.advice[i].reason
              }
              return (root.advice.length > 0) ? (root.advice[0].label + " \u00b7 " + root.advice[0].reason) : ""
            }
            color: root.mutedColor
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 10
            wrapMode: Text.WordWrap
          }

          // 2-hour rain nowcast bar chart
          Item {
            Layout.fillWidth: true
            implicitHeight: 66
            visible: root.nowcast && root.nowcast.series && root.nowcast.series.length > 0

            ColumnLayout {
              anchors.fill: parent
              spacing: 4

              RowLayout {
                Layout.fillWidth: true
                Text {
                  text: "Buienradar (komende 2 uur)"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 11
                  font.bold: true
                }
                Item { Layout.fillWidth: true }
                Text {
                  text: root.nowcast ? (root.nowcast.summary || "") : ""
                  color: (root.nowcast && root.nowcast.raining_now)
                    ? (root.bar ? root.bar.urgent : "#4fa3e0") : root.mutedColor
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                }
              }

              Item {
                Layout.fillWidth: true
                implicitHeight: 46

                Row {
                  id: rainGraph
                  anchors.fill: parent
                  anchors.bottomMargin: 14
                  spacing: 1

                  Repeater {
                    model: (root.nowcast && root.nowcast.series) ? root.nowcast.series : []
                    delegate: Item {
                      width: (rainGraph.width - ((root.nowcast.series.length || 1) - 1)) / (root.nowcast.series.length || 1)
                      height: rainGraph.height

                      Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        radius: 1
                        height: Math.max(modelData.mm >= 0.05 ? 2 : 1,
                                         Math.min(1, Math.sqrt(modelData.mm / 4.0)) * parent.height)
                        color: modelData.mm >= 0.05
                          ? (root.bar ? root.bar.urgent : "#4fa3e0")
                          : (root.bar ? root.bar.foreground : "#666")
                        opacity: modelData.mm >= 0.05 ? 0.95 : 0.2
                      }
                    }
                  }
                }

                // Time labels
                Text {
                  anchors.left: parent.left
                  anchors.bottom: parent.bottom
                  text: (root.nowcast && root.nowcast.series && root.nowcast.series.length) ? root.nowcast.series[0].time : ""
                  color: root.mutedColor
                  font.pixelSize: 9
                }
                Text {
                  anchors.horizontalCenter: parent.horizontalCenter
                  anchors.bottom: parent.bottom
                  text: (root.nowcast && root.nowcast.series && root.nowcast.series.length > 12) ? root.nowcast.series[12].time : ""
                  color: root.mutedColor
                  font.pixelSize: 9
                }
                Text {
                  anchors.right: parent.right
                  anchors.bottom: parent.bottom
                  text: (root.nowcast && root.nowcast.series && root.nowcast.series.length) ? root.nowcast.series[root.nowcast.series.length - 1].time : ""
                  color: root.mutedColor
                  font.pixelSize: 9
                }
              }
            }
          }

          // Zonnestand
          RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.solar && root.solar.phase !== undefined

            Text {
              text: "\u2600 Zon: " + (root.solar.phase || "")
                    + " (" + (root.solar.now_elev !== undefined ? root.solar.now_elev + "°" : "") + ")"
              color: root.mutedColor
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 10
            }
            Item { Layout.fillWidth: true }
            Text {
              text: (root.solar.rise || "--") + " \u2191 \u00b7 " + (root.solar.set || "--") + " \u2193"
              color: root.mutedColor
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 10
            }
          }

          // External live weather links
          RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: windyHover.hovered ? Qt.rgba(0.22, 0.74, 0.97, 0.2) : Qt.rgba(0.22, 0.74, 0.97, 0.08)
              border.width: 1
              border.color: Qt.rgba(0.22, 0.74, 0.97, 0.3)

              HoverHandler { id: windyHover }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.bar.run("xdg-open 'https://www.windy.com/?' + root.lat + ',' + root.lon + ',5'")
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 5
                Text { text: "\u{1F300}"; font.pixelSize: 10 }
                Text {
                  text: "Windy Live 3D Aardbol \u2197"
                  color: "#38bdf8"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                  font.bold: true
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: buienHover.hovered ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.12)

              HoverHandler { id: buienHover }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.bar.run("xdg-open https://www.buienradar.nl")
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 5
                Text { text: "\u{1F327}"; font.pixelSize: 10 }
                Text {
                  text: "Buienradar.nl \u2197"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                  font.bold: true
                }
              }
            }
          }
        }

        // ====================================================================
        // TAB 2: VLUCHTEN & RADAR
        // ====================================================================
        ColumnLayout {
          Layout.fillWidth: true
          visible: root.currentTab === "vluchten"
          spacing: 8

          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "Vluchtradar (" + root.planeCount + " lokaal · " + root.militaryCount + " militair mondiaal)"
              color: root.bar ? root.bar.foreground : "#fff"
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 12
              font.bold: true
            }
            Item { Layout.fillWidth: true }
            Text {
              text: (root.emergencies && root.emergencies.length > 0)
                ? ("\u26A0 " + root.emergencies.length + " noodgeval")
                : (root.militaryNearby.length > 0 ? ("🎖️ " + root.militaryNearby.length + " militair nabij") : "adsb.lol")
              color: (root.emergencies && root.emergencies.length > 0)
                ? (root.bar ? root.bar.urgent : "#d9534f")
                : (root.militaryNearby.length > 0 ? "#f59e0b" : root.mutedColor)
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 10
            }
          }

          // Polar Radar Scope
          Item {
            Layout.fillWidth: true
            implicitHeight: 200

            Canvas {
              id: scopeCanvas
              anchors.fill: parent
              property var planes: root.aircraft
              property int maxNm: root.radiusNm
              property int hover: root.hoveredPlane
              onPlanesChanged: requestPaint()
              onHoverChanged: requestPaint()

              onPaint: {
                var ctx = getContext("2d")
                var w = width, h = height
                ctx.reset()
                ctx.clearRect(0, 0, w, h)

                var cx = w / 2, cy = h / 2
                var R = Math.min(w, h) / 2 - 12
                var fg = root.bar ? root.bar.foreground : "#cacccc"

                // Range rings
                ctx.strokeStyle = Qt.rgba(0.44, 0.47, 0.50, 0.35)
                ctx.lineWidth = 1
                for (var f = 0.25; f <= 1.001; f += 0.25) {
                  ctx.beginPath()
                  ctx.arc(cx, cy, R * f, 0, Math.PI * 2)
                  ctx.stroke()
                }

                // Spokes
                ctx.beginPath()
                ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy)
                ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R)
                ctx.stroke()

                // Cardinals
                ctx.fillStyle = Qt.rgba(0.44, 0.47, 0.50, 0.9)
                ctx.font = "9px sans-serif"
                ctx.textAlign = "center"
                ctx.fillText("N", cx, cy - R - 3)
                ctx.fillText("Z", cx, cy + R + 9)
                ctx.fillText("W", cx - R - 7, cy + 3)
                ctx.fillText("O", cx + R + 7, cy + 3)

                // Centre
                ctx.fillStyle = fg
                ctx.beginPath()
                ctx.arc(cx, cy, 2.5, 0, Math.PI * 2)
                ctx.fill()

                var maxKm = scopeCanvas.maxNm * 1.852
                var arr = scopeCanvas.planes || []
                for (var i = 0; i < arr.length; i++) {
                  var a = arr[i]
                  if (a.dist_km === undefined || a.bearing === undefined) continue
                  var frac = Math.log(1 + a.dist_km) / Math.log(1 + maxKm)
                  frac = Math.max(0, Math.min(1, frac))
                  var rad = (a.bearing - 90) * Math.PI / 180
                  var px = cx + Math.cos(rad) * R * frac
                  var py = cy + Math.sin(rad) * R * frac

                  var isHover = (i === scopeCanvas.hover)
                  var emerg = a.emergency === true
                  var alt = (a.alt_ft === null || a.alt_ft === undefined) ? 30000 : a.alt_ft
                  var t = Math.max(0, Math.min(1, alt / 40000))
                  var col = emerg ? "#e05555"
                          : Qt.rgba(0.35 + 0.45 * (1 - t), 0.65 + 0.2 * t, 0.45 + 0.45 * t, 1)

                  var hdg = (a.track !== null && a.track !== undefined ? a.track : a.bearing)
                  var hr = (hdg - 90) * Math.PI / 180
                  var size = isHover ? 6.5 : 4.5
                  ctx.fillStyle = col
                  ctx.beginPath()
                  ctx.moveTo(px + Math.cos(hr) * size, py + Math.sin(hr) * size)
                  ctx.lineTo(px + Math.cos(hr + 2.5) * size * 0.75, py + Math.sin(hr + 2.5) * size * 0.75)
                  ctx.lineTo(px + Math.cos(hr - 2.5) * size * 0.75, py + Math.sin(hr - 2.5) * size * 0.75)
                  ctx.closePath()
                  ctx.fill()

                  if (isHover || emerg) {
                    ctx.strokeStyle = col
                    ctx.lineWidth = 1.2
                    ctx.beginPath()
                    ctx.arc(px, py, size + 3, 0, Math.PI * 2)
                    ctx.stroke()
                  }
                }
              }
            }
          }

          // Nearest aircraft items
          Repeater {
            model: root.aircraft.slice(0, 3)
            delegate: Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: root.hoveredPlane === index ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.03)
              border.width: 1
              border.color: modelData.emergency ? "#d9534f" : Qt.rgba(1, 1, 1, 0.06)

              HoverHandler {
                onHoveredChanged: root.hoveredPlane = hovered ? index : -1
              }

              RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8

                Text {
                  text: (modelData.callsign || modelData.hex) + (modelData.type ? (" (" + modelData.type + ")") : "")
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                  font.bold: true
                }
                Item { Layout.fillWidth: true }
                Text {
                  text: (modelData.alt_ft != null ? modelData.alt_ft + " ft" : "")
                        + (modelData.speed_kt != null ? " · " + modelData.speed_kt + " kt" : "")
                        + " · " + modelData.dist_km + " km " + modelData.compass
                  color: root.mutedColor
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                }
              }
            }
          }

          // Nearby military aircraft
          RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 2
            visible: root.militaryNearby.length > 0
            spacing: 6
            Text {
              text: "Militaire vluchten binnen 500km"
              color: "#f59e0b"
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 11
              font.bold: true
            }
          }

          Repeater {
            model: root.militaryNearby.slice(0, 3)
            delegate: Rectangle {
              Layout.fillWidth: true
              implicitHeight: 22
              radius: 3
              color: Qt.rgba(0.96, 0.62, 0.04, 0.08)
              border.width: 1
              border.color: Qt.rgba(0.96, 0.62, 0.04, 0.25)

              RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8

                Text {
                  text: "🎖️ " + (modelData.callsign || modelData.hex) + (modelData.type ? (" (" + modelData.type + ")") : "")
                  color: "#f59e0b"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                  font.bold: true
                }
                Item { Layout.fillWidth: true }
                Text {
                  text: (modelData.alt_ft != null ? modelData.alt_ft + " ft" : "grond")
                        + (modelData.speed_kt != null ? " · " + modelData.speed_kt + " kt" : "")
                        + " · " + modelData.dist_km + " km"
                  color: root.mutedColor
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                }
              }
            }
          }

          // METAR Flight categories
          RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 8

            Text {
              text: "Vliegweer (METAR):"
              color: root.bar ? root.bar.foreground : "#ddd"
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 11
              font.bold: true
            }

            Repeater {
              model: [
                { k: "VFR",  col: "#5cb85c" },
                { k: "MVFR", col: "#5bc0de" },
                { k: "IFR",  col: "#d9534f" },
                { k: "LIFR", col: "#d17ad1" }
              ]
              delegate: Rectangle {
                visible: root.metarCounts[modelData.k] !== undefined && root.metarCounts[modelData.k] > 0
                radius: 3
                implicitWidth: catRow.implicitWidth + 8
                implicitHeight: 18
                color: Qt.rgba(1, 1, 1, 0.05)
                border.width: 1
                border.color: modelData.col

                RowLayout {
                  id: catRow
                  anchors.centerIn: parent
                  spacing: 4
                  Text {
                    text: "\u25CF"
                    color: modelData.col
                    font.pixelSize: 9
                  }
                  Text {
                    text: root.metarCounts[modelData.k] + " " + modelData.k
                    color: root.bar ? root.bar.foreground : "#ddd"
                    font.family: root.bar ? root.bar.fontFamily : ""
                    font.pixelSize: 9
                  }
                }
              }
            }
          }
        }

        // ====================================================================
        // TAB 3: MILIEU & WERELD
        // ====================================================================
        ColumnLayout {
          Layout.fillWidth: true
          visible: root.currentTab === "milieu"
          spacing: 8

          Text {
            Layout.fillWidth: true
            text: "Luchtkwaliteit & Pollen"
            color: root.bar ? root.bar.foreground : "#ddd"
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 12
            font.bold: true
          }

          Repeater {
            model: [
              { k: "european_aqi", label: "Luchtindex", suffix: "" },
              { k: "pm2_5",        label: "PM2.5",      suffix: " \u00b5g/m\u00b3" },
              { k: "pm10",         label: "PM10",       suffix: " \u00b5g/m\u00b3" },
              { k: "ammonia",      label: "Ammoniak",   suffix: " \u00b5g/m\u00b3" }
            ]
            delegate: RowLayout {
              Layout.fillWidth: true
              visible: root.air[modelData.k] !== undefined && root.air[modelData.k] !== null
              spacing: 8

              Text {
                Layout.preferredWidth: 80
                text: modelData.label
                color: root.mutedColor
                font.family: root.bar ? root.bar.fontFamily : ""
                font.pixelSize: 11
              }
              Text {
                Layout.fillWidth: true
                text: {
                  var v = root.air[modelData.k]
                  if (v === undefined || v === null) return ""
                  var extra = ""
                  if (modelData.k === "european_aqi" && root.air.aqi_label)
                    extra = "  " + root.air.aqi_label
                  if (modelData.k === "ammonia" && root.air.ammonia_label)
                    extra = "  " + root.air.ammonia_label
                  return v + modelData.suffix + extra
                }
                color: {
                  if (modelData.k === "ammonia" && root.air.ammonia >= 15) return "#e0b34f"
                  if (modelData.k === "european_aqi" && root.air.european_aqi > 40) return "#e0b34f"
                  return root.bar ? root.bar.foreground : "#ddd"
                }
                font.family: root.bar ? root.bar.fontFamily : ""
                font.pixelSize: 11
              }
            }
          }

          Text {
            Layout.fillWidth: true
            Layout.topMargin: 2
            text: {
              var names = { alder: "els", birch: "berk", grass: "gras",
                            mugwort: "bijvoet", olive: "olijf", ragweed: "ambrosia" }
              var parts = []
              for (var k in root.pollen) {
                var v = root.pollen[k]
                if (v !== null && v !== undefined && v > 0)
                  parts.push((names[k] || k) + " " + v)
              }
              return parts.length > 0 ? ("Pollen: " + parts.join(" \u00b7 ")) : "Pollen: geen actieve pollen gemeten"
            }
            color: root.mutedColor
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 10
            wrapMode: Text.WordWrap
          }

          Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Qt.rgba(1, 1, 1, 0.08)
          }

          // Global Disasters & Earthquakes count
          Text {
            Layout.fillWidth: true
            text: "Geopolitiek & Wereld (World Monitor)"
            color: root.bar ? root.bar.foreground : "#ddd"
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 12
            font.bold: true
          }

          RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Repeater {
              model: [
                { icon: "⚓", label: "Knelpunten", count: root.waterways.length || 11 },
                { icon: "🔥", label: "Hotspots",   count: root.hotspots.length || 9 },
                { icon: "☢️", label: "Nucleair",   count: root.nuclear.length || 19 },
                { icon: "🎖️", label: "Bases",      count: root.militaryBases.length || 14 }
              ]
              delegate: Rectangle {
                Layout.fillWidth: true
                implicitHeight: 26
                radius: 3
                color: Qt.rgba(1, 1, 1, 0.04)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.1)

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 4
                  Text {
                    text: modelData.icon
                    font.pixelSize: 10
                  }
                  Text {
                    text: modelData.count + " " + modelData.label
                    color: root.bar ? root.bar.foreground : "#ddd"
                    font.family: root.bar ? root.bar.fontFamily : ""
                    font.pixelSize: 9
                    font.bold: true
                  }
                }
              }
            }
          }

          // Toolbelt Infrastructure & Space Weather
          RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Repeater {
              model: [
                { icon: "🌐", label: "Kabels", count: root.submarineCables.length || 35 },
                { icon: "🛢️", label: "Pijplijn", count: root.pipelines.length || 32 },
                { icon: "🏢", label: "Datacenters", count: root.datacenters.length || 39 },
                { icon: "🧲", label: "Ruimteweer", count: (root.spaceWeather && root.spaceWeather.kp != null) ? ("Kp " + root.spaceWeather.kp) : "Kp 2" }
              ]
              delegate: Rectangle {
                Layout.fillWidth: true
                implicitHeight: 26
                radius: 3
                color: Qt.rgba(1, 1, 1, 0.04)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.1)

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 4
                  Text {
                    text: modelData.icon
                    font.pixelSize: 10
                  }
                  Text {
                    text: (typeof modelData.count === "number" ? (modelData.count + " ") : (modelData.count + " · ")) + modelData.label
                    color: root.bar ? root.bar.foreground : "#ddd"
                    font.family: root.bar ? root.bar.fontFamily : ""
                    font.pixelSize: 9
                    font.bold: true
                  }
                }
              }
            }
          }

          Text {
            Layout.fillWidth: true
            text: (root.disasters ? root.disasters.length : 0) + " GDACS rampen · "
                  + (root.quakes ? root.quakes.length : 0) + " aardbevingen (USGS M2.5+) · "
                  + (root.militaryCount > 0 ? root.militaryCount + " militaire vluchten · " : "")
                  + ((root.spaceWeather && root.spaceWeather.kp_label) ? ("Zon/Kp: " + root.spaceWeather.kp_label) : "")
            color: root.mutedColor
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 10
            wrapMode: Text.WordWrap
          }

          // Drone No-Fly & Scheepvaart live status
          RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 28
              radius: 4
              color: (root.droneStatus && root.droneStatus.status === "prohibited")
                ? Qt.rgba(0.9, 0.2, 0.2, 0.15)
                : Qt.rgba(0.2, 0.8, 0.4, 0.12)
              border.width: 1
              border.color: (root.droneStatus && root.droneStatus.status === "prohibited")
                ? "#ef4444" : "#22c55e"

              RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6
                Text { text: "🚁"; font.pixelSize: 11 }
                Text {
                  Layout.fillWidth: true
                  text: (root.droneStatus && root.droneStatus.headline) ? root.droneStatus.headline : "Drone status checken"
                  color: (root.droneStatus && root.droneStatus.status === "prohibited") ? "#fca5a5" : "#86efac"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                  elide: Text.ElideRight
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 28
              radius: 4
              color: Qt.rgba(0.2, 0.6, 0.9, 0.12)
              border.width: 1
              border.color: "#38bdf8"

              RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6
                Text { text: "🚢"; font.pixelSize: 11 }
                Text {
                  Layout.fillWidth: true
                  text: (root.vessels && root.vessels.count)
                    ? (root.vessels.count + " schepen (" + (root.vessels.active_moving || 0) + " varend)")
                    : "Scheepvaart AIS"
                  color: "#7dd3fc"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                  elide: Text.ElideRight
                }
              }
            }
          }

          // Treinen & Webcams status
          RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 28
              radius: 4
              color: Qt.rgba(0.9, 0.6, 0.1, 0.12)
              border.width: 1
              border.color: "#f59e0b"

              RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6
                Text { text: "🚆"; font.pixelSize: 11 }
                Text {
                  Layout.fillWidth: true
                  text: (root.trains && root.trains.length)
                    ? (root.trains.length + " treinen op het spoor")
                    : "Treinen monitoring"
                  color: "#fde68a"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                  elide: Text.ElideRight
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 28
              radius: 4
              color: Qt.rgba(0.6, 0.3, 0.9, 0.12)
              border.width: 1
              border.color: "#a855f7"

              RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6
                Text { text: "📷"; font.pixelSize: 11 }
                Text {
                  Layout.fillWidth: true
                  text: (root.webcams && root.webcams.length)
                    ? (root.webcams.length + " live HD webcams")
                    : "Live webcams"
                  color: "#e9d5ff"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                  elide: Text.ElideRight
                }
              }
            }
          }

          // Quick launch buttons for Drone, Marine, Google Maps, Stellarium, 3D
          RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: droneHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.15)
              HoverHandler { id: droneHover }
              TapHandler {
                onTapped: Qt.openUrlExternally("https://map.godrone.nl/")
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 4
                Text { text: "🚁"; font.pixelSize: 10 }
                Text {
                  text: "GoDrone ↗"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: marineHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.15)
              HoverHandler { id: marineHover }
              TapHandler {
                onTapped: Qt.openUrlExternally("https://www.marinetraffic.com/")
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 4
                Text { text: "🚢"; font.pixelSize: 10 }
                Text {
                  text: "Marine ↗"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: gmapsHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.15)
              HoverHandler { id: gmapsHover }
              TapHandler {
                onTapped: Qt.openUrlExternally("https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=" + root.lat + "," + root.lon)
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 4
                Text { text: "🚶"; font.pixelSize: 10 }
                Text {
                  text: "Street View ↗"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }
          }

          RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: spaceHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.15)
              HoverHandler { id: spaceHover }
              TapHandler {
                onTapped: Qt.openUrlExternally("https://stellarium-web.org/")
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 4
                Text { text: "🌌"; font.pixelSize: 10 }
                Text {
                  text: "Stellarium ↗"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: fly3dHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.15)
              HoverHandler { id: fly3dHover }
              TapHandler {
                onTapped: Qt.openUrlExternally("https://earth.google.com/web/@" + root.lat + "," + root.lon + ",250a,4500d,35y,0h,60t,0r")
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 4
                Text { text: "✈️"; font.pixelSize: 10 }
                Text {
                  text: "3D Flyover ↗"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: camHover.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.04)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.15)
              HoverHandler { id: camHover }
              TapHandler {
                onTapped: root.openMap()
              }
              RowLayout {
                anchors.centerIn: parent
                spacing: 4
                Text { text: "📷"; font.pixelSize: 10 }
                Text {
                  text: "Webcams (k)"
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }
          }

          // Breaking RSS News feed
          Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Qt.rgba(1, 1, 1, 0.08)
            visible: root.news.length > 0
          }

          RowLayout {
            Layout.fillWidth: true
            visible: root.news.length > 0
            Text {
              text: "Laatste Wereldnieuws (RSS)"
              color: root.bar ? root.bar.foreground : "#ddd"
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 12
              font.bold: true
            }
            Item { Layout.fillWidth: true }
            Text {
              text: "NOS · BBC · Al Jazeera"
              color: root.mutedColor
              font.family: root.bar ? root.bar.fontFamily : ""
              font.pixelSize: 9
            }
          }

          Repeater {
            model: root.news.slice(0, 3)
            delegate: Rectangle {
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 3
              color: newsHover.hovered ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.03)
              border.width: 1
              border.color: Qt.rgba(1, 1, 1, 0.08)

              HoverHandler { id: newsHover }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  if (modelData.link) root.bar.run("xdg-open '" + modelData.link + "'")
                }
              }

              RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 6

                Text {
                  text: "[" + modelData.source + "]"
                  color: "#eab308"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 9
                  font.bold: true
                }
                Text {
                  Layout.fillWidth: true
                  text: modelData.title || ""
                  color: root.bar ? root.bar.foreground : "#ddd"
                  font.family: root.bar ? root.bar.fontFamily : ""
                  font.pixelSize: 10
                  elide: Text.ElideRight
                }
              }
            }
          }
        }

        Rectangle {
          Layout.fillWidth: true
          implicitHeight: 1
          color: Qt.rgba(1, 1, 1, 0.08)
        }

        // Footer info & shortcuts
        RowLayout {
          Layout.fillWidth: true
          Text {
            text: "Open-Meteo \u00b7 Buienradar \u00b7 adsb.lol \u00b7 World Monitor \u00b7 USGS \u00b7 GDACS \u00b7 RSS"
            color: root.mutedColor
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 9
          }
          Item { Layout.fillWidth: true }
          Text {
            text: "1/2/3 tab \u00b7 k kaart \u00b7 r verversen"
            color: root.mutedColor
            font.family: root.bar ? root.bar.fontFamily : ""
            font.pixelSize: 9
          }
        }
      }
    }
  }
}
