<div id="integromatCredentialsModal" class="modal fade">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">

            <div class="modal-header">
                <h3>Connect an Integromat Account</h3>
            </div>

            <form>
                <div class="modal-body">

                    <div class="row">
                        <div class="col-sm-6">
                            <div class="form-group">
                                <label for="apiToken">API Token</label>
                                    <!-- Link to API token generation page -->
                                    <a href="https://apidocs.integromat.com/"
                                       target="_blank" class="text-muted addon-external-link">
                                        (Get from Integromat <i class="fa fa-external-link-square"></i>)
                                    </a>
                                <input class="form-control" data-bind="value: integromatApiToken" id="integromat_api_token" name="integromat_Api_Token" />
                            </div>
                        </div>
                    </div><!-- end row -->

                    <!-- Flashed Messages -->
                    <div class="help-block">
                        <p data-bind="html: message, attr: {class: messageClass}"></p>
                    </div>

                </div><!-- end modal-body -->

                <div class="modal-footer">

                    <a href="#" class="btn btn-default" data-bind="click: clearModal" data-dismiss="modal">Cancel</a>

                    <!-- Save Button -->
                    <button data-bind="click: connectAccount" class="btn btn-success">Save</button>

                </div><!-- end modal-footer -->

            </form>

        </div><!-- end modal-content -->
    </div>
</div>

<div id="manageWebMeetingAppsAttendeesModal" class="modal fade">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Manage Web Meeting Apps Attendees</h3>
            </div>
            <div class="modal-body">

                <div id="ManageWebMeetingAttendees">
                    <ul class="nav nav-tabs">
                        <li class="active"><a href="#addAttendees" data-toggle="tab">${_("Add")}</a></li>
                        <li><a href="#deleteAttendees" data-toggle="tab">${_("Delete")}</a></li>
                    </ul>
                    <div class="tab-content">
                        <div class="m-t-md tab-pane active" id="addAttendees">
                            <div data-bind="template: {name: 'addWebMeetingAttendees'}"></div>
                    </div>
                    <div class="m-t-md tab-pane" id="deleteAttendees">
                        <div data-bind="template: {name: 'deleteWebMeetingAttendees'}"></div>
                    </div>
                </div>
            </div>

            <script id="addWebMeetingAttendees" type="text/html">
                <form>
                    <div>
                        <label>User Guid</label>
                        <input type="text" data-bind="value: userGuid" placeholder="Enter the User Guid">
                    </div>
                    <div>
                        <label style="padding-top: 10px;">Microsoft Teams</label>
                    </div>
                    <div style="padding-left: 25px;">
                        <label>Sign-in Address</label>
                        <input type="text" data-bind="value: microsoftTeamsMail" placeholder="Enter the Microsoft Teams Sign-in Address">
                    </div>
                    <div style="padding-left: 25px;">
                        <label>User Name</label>
                        <input type="text" data-bind="value: microsoftTeamsUserName" placeholder="Enter the Microsoft Teams User Name">
                    </div>
                    <div style="padding-top: 10px;">
                        <label>Webex Meetings</label>
                    </div>
                        <div style="padding-left: 25px;">
                            <label>Sign-in Address</label>
                            <input type="text" data-bind="value: webexMeetingsMail" placeholder="Enter the Webex Meetings Sign-in Address">
                        </div>
                    <div style="padding-left: 25px;">
                        <label>Display Name</label>
                        <input type="text" data-bind="value: webexMeetingsDisplayName" placeholder="Enter the Webex Meetings Display Name">
                    </div>
                </form>
                <!-- Flashed Messages -->
                <div class="help-block">
                    <p data-bind="html: message, attr: {class: messageClass}"></p>
                </div>
            </scirpt>

            <script id="deleteWebMeetingAttendees" type="text/html">
                <form>
                    <div>
                        <label>User Guid</label>
                        <input type="text" data-bind="value: userGuidToDelete" placeholder="Enter the User Guid">
                    </div>
                </form>
                <!-- Flashed Messages -->
                <div class="help-block">
                    <p data-bind="html: message, attr: {class: messageClass}"></p>
                </div>
            </scirpt>
            </div><!-- end modal-body -->

        </div><!-- end modal-content -->
    </div>
</div>