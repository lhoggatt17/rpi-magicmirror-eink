var config = {
  address: "localhost",
  port: 8080,
  ipWhitelist: [],
  language: "de",
  timeFormat: 24,
  units: "metric",
  modules: [
    {
      module: "calendar_monthly",
      position: "top_left",
      config: {
      }
    },
    {
      module: "weatherforecast",
      position: "top_right",
      header: "Wien",
      config: {
        appendLocationNameToHeader: false,
        animationSpeed: 0,
        fade: false,
        location: "Vienna",
        appid: "OPEN_WEATHER_API_KEY"
      }
    },
    {
      module: "currentweather",
      position: "top_right",
      config: {
        appendLocationNameToHeader: false,
        animationSpeed: 0,
        fade: false,
        location: "Vienna",
        appid: "OPEN_WEATHER_API_KEY"
      }
    },
    {
      module: "clock",
      position: "middle_center",
      config: {
        showWeek: true
      }
    },
    {
      module: "compliments",
      position: "middle_center",
      config: {
        fadeSpeed: 0
      }
    },
    {
      module: "calendar",
      header: "Geburtstage",
      position: "bottom_bar",
      config: {
        maximumEntries: 10,
        maxTitleLength: 40,
        fetchInterval: 3600000, // every 60 min
        animationSpeed: 0,
        fade: false,
        dateFormat: "DD.MM.",
        fullDayEventDateFormat: "DD.MM.",
        timeFormat: "absolute",
        urgency: 7,
        wrapEvents: true,
        displayRepeatingCountTitle: false,
        calendars: [
          {
            symbol: "calendar-check-o",
            url: "webcal://www.calendarlabs.com/ical-calendar/ics/46/Germany_Holidays.ics"
          }
        ]
      }
    },
  ]
};

/*************** DO NOT EDIT THE LINE BELOW ***************/
if (typeof module !== "undefined") {module.exports = config;}
