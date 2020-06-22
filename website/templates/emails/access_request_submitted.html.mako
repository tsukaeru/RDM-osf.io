<%inherit file="notify_base.mako" />

<%def name="content()">
<tr>
  <td style="border-collapse: collapse;">
    <%!
        from website import settings
    %>
    こんにちは、${requester.fullname}さん<br>
    <br>
    <a href="${requester.absolute_url}">${requester.fullname}</a> has requested access to your ${node.project_or_component} "<a href="${node.absolute_url}">${node.title}</a>."<br>
    <br>
    申請をレビューするには<a href="${contributors_url}">こちら</a>をクリックしてください。アクセスの許可/拒否および権限設定ができます。<br>
    <br>
    あなたのプロジェクトで「アクセス申請」の機能が有効になっているために申請が送られています。共同作業を希望する人がいれば、この機能を使ってあなたのプロジェクトに参加させることができます。機能を無効化するには<a href="${project_settings_url}">こちら</a>をクリックしてください。<br>
    <br>
    よろしくお願いいたします。<br>
    <br>
    The GRDMチーム<br>
    <br>
    詳細をご希望ですか？　GRDMについてはhttps://rdm.nii.ac.jp/を、支持機構である国立情報学研究所についてはhttps://nii.ac.jp/をご覧ください。<br>
    <br>
    お問い合わせはrdm_support@nii.ac.jpまでお願いいたします。<br>


</tr>
<tr>
  <td style="border-collapse: collapse;">
    <%!
        from website import settings
    %>
    Hello ${admin.fullname},<br>
    <br>
    <a href="${requester.absolute_url}">${requester.fullname}</a> has requested access to your ${node.project_or_component} "<a href="${node.absolute_url}">${node.title}</a>."<br>
    <br>
    To review the request, click <a href="${contributors_url}">here</a> to allow or deny access and configure permissions.<br>
    <br>
    This request is being sent to you because your project has the 'Request Access' feature enabled. This allows potential collaborators to request to be added to your project. To disable this feature, click <a href="${project_settings_url}">here</a>.<br>
    <br>
    Sincerely,<br>
    <br>
    The GRDM Team<br>
    <br>
    Want more information? Visit https://rdm.nii.ac.jp/ to learn about GRDM, or https://nii.ac.jp/ for information about its supporting organization, the National Institute of Informatics.<br>
    <br>
    Questions? Email ${osf_contact_email}<br>


</tr>
</%def>
