'use strict';
// widget用ファイル

var $ = require('jquery');
var ko = require('knockout');
var Raven = require('raven-js');
var osfHelpers = require('js/osfHelpers');
var moment = require('moment');
var logPrefix = '[integromat] ';

require('./integromat.css');


function IntegromatWidget() {
    var self = this;
    self.baseUrl = window.contextVars.node.urls.api + 'integromat/';
    self.loading = ko.observable(true);
    self.loadFailed = ko.observable(false);
    self.loadCompleted = ko.observable(false);
    self.todaysMeetings = ko.observable('');
    self.tomorrowsMeetings = ko.observable('');

    var now = new Date();
    self.today = (now.getMonth() + 1) + '/' + now.getDate();
    self.tomorrow = (now.getMonth() + 1) + '/' + (now.getDate() + 1)

    var now = new Date();
    var sTodayLocal = new Date(now.setHours(0, 0, 0, 0));
    var offsetHours = now.getTimezoneOffset() / 60;
    var sTodayUtc = new Date(now.setHours(now.getHours() + offsetHours));
    var sTomorrowUtc = new Date(sTodayUtc.setDate(sTodayUtc.getDate() + 1));
    var sDayAfterTomorrowUtc = new Date(sTodayUtc.setDate(sTodayUtc.getDate() + 2));

    self.loadConfig = function() {
        var url = self.baseUrl + 'get_meetings';
        console.log(logPrefix, 'loading: ', url);

        return $.ajax({
            url: url,
            type: 'GET',
            dataType: 'json'
        }).done(function (data) {
            console.log(logPrefix, 'loaded: ', data);
            self.loading(false);
            self.loadCompleted(true);
            const recentMeetings = data.recentMeetings;
            var todaysMeetings = [];
            var tomorrowsMeetings = [];
            var start_datetime;

            for(var i = 0; i < recentMeetings.length; i++){

                start_datetime = new Date(recentMeetings[i].fields.start_datetime);

                if(sTodayUtc <= start_datetime && start_datetime < sTomorrowUtc){
                    todaysMeetings.push(recentMeetings[i]);
                }else if(sTomorrowUtc <= start_datetime && start_datetime < sDayAfterTomorrowUtc){
                    tomorrowsMeetings.push(recentMeetings[i]);
                }
            }
            self.todaysMeetings(todaysMeetings);
            self.tomorrowsMeetings(tomorrowsMeetings);
        }).fail(function(xhr, status, error) {
            self.loading(false);
            self.loadFailed(true);
            Raven.captureMessage('Error while retrieving addon info', {
                extra: {
                    url: url,
                    status: status,
                    error: error
                }
            });
        });
    };

    self.startMeeting = function(url) {
        window.open(url, '_blank');
    };

}

var w = new IntegromatWidget();
osfHelpers.applyBindings(w, '#integromat-content');
w.loadConfig();
