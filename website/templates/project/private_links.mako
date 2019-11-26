<%include file="modal_generate_private_link.mako"/>
<link rel="stylesheet" href="/static/css/private_links_table.css">
<div class="scripted" id="linkScope">
    <table id="privateLinkTable" class="table responsive-table responsive-table-xs"
            data-bind="visible: visible">
        <thead>
            <tr>
                <th class="responsive-table-hide">${ _("Link Name") }</th>
                <th class="shared-comp">${ _("Shared Components") }</th>
                <th>${ _("Created Date") }</th>
                <th>${ _("Created By") }</th>
                <th class="min-width">${ _("Anonymous") }</th>
                <th class="min-width"></th>
            </tr>
        </thead>
        <tbody data-bind="template: {
                    name: 'linkTbl',
                    foreach: privateLinks,
                    afterRender: afterRenderLink
                }">
        </tbody>
    </table>
</div>
<%include file="private_links_table.mako"/>
