
function loadDateTimePlayer() {
    $('input[name="datetimes"]').daterangepicker({
        "showISOWeekNumbers": true,
        "timePicker": true,
        "timePicker24Hour": true,
        "timePickerSeconds": true,
        "autoApply": true,
        ranges: {
            'Today': [moment().startOf('day'), moment().endOf('day')],
            'Yesterday': [moment().subtract(1, 'days').startOf('day'), moment().subtract(1, 'days').endOf('day')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment().endOf('day')],
            'Last 30 Days': [moment().subtract(29, 'days'), moment().endOf('day')],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        "locale": {
            "format": "MM/DD/YYYY HH:mm:ss",
            "separator": " - ",
            "applyLabel": "Apply",
            "cancelLabel": "Cancel",
            "fromLabel": "From",
            "toLabel": "To",
            "customRangeLabel": "Custom",
            "weekLabel": "W",
            "daysOfWeek": [
                "Su",
                "Mo",
                "Tu",
                "We",
                "Th",
                "Fr",
                "Sa"
            ],
            "monthNames": [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ],
            "firstDay": 1
        },
        "startDate": moment().subtract(6, 'days').startOf('day'),
        "endDate": moment().endOf('day')
    });
}




var downloadedData = [];
loadDateTimePlayer();
var stationTable = document.getElementById('stations');

var stations = new Handsontable(stationTable, {
  data:downloadedData,
  stretchH: 'all',
  colHeaders: ['Hardware Address', 'Date', 'download'],
  columns: [
    {
      data: 'hwa',
      readOnly: true,
      editor: false
    },
    {
      data: 'timestamp',
      readOnly: true,
      editor: false
    },
    {
      data: 'id',
      renderer: 'html',
      type: 'text',
      readOnly: true,
      editor: false
    },
  ]
});