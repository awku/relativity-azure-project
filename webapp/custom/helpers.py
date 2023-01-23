from os.path import splitext
from types import SimpleNamespace
from uuid import uuid4
import requests
from json import loads, dumps


def randomize_path(instance, filename):
    extension = splitext(filename)[1]
    return 'image_{0}_{1}{2}'.format(instance.slug, uuid4(), extension)


def get_aad_b2c_config(config):
    config_tenant_name = (config.tenant_name).split(".")[0]
    dict_data = {
        "type": {"client_type": "CONFIDENTIAL", "authority_type": "B2C", "framework": "DJANGO"},
        "client": {"client_id": config.client_id,
                   "client_credential": config.client_credential,
                   "authority": f"https://{config_tenant_name}.b2clogin.com/{config_tenant_name}.onmicrosoft.com"},
        "b2c": {"susi": "/b2c_1_signupsignin", "profile": "/b2c_1_editprofile", "password": "/b2c_1_resetpassword"},
        "auth_request": {"redirect_uri": None, "scopes": [""], "response_type": "code"},
        "django": {"id_web_configs": "MS_ID_WEB_CONFIGS",
                   "auth_endpoints": {"prefix": "auth", "sign_in": "sign_in", "edit_profile": "edit_profile",
                                      "redirect": "redirect", "sign_out": "sign_out", "post_sign_out": "post_sign_out"}},
        "flask": None}
    return loads(dumps(dict_data), object_hook=lambda d: SimpleNamespace(**d))


def is_member_of_admins(oid, config):
    graphAccessUrl = f'https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token'
    graphTokenBody = f'client_id={config.client_id}&scope=https%3A%2F%2Fgraph.microsoft.com%2F.default&client_secret={config.client_credential}&grant_type=client_credentials'
    graphUsersUrl = f'https://graph.microsoft.com/v1.0/users/{oid}/memberOf'
    tokenResponse = requests.post(graphAccessUrl, graphTokenBody)
    token = tokenResponse.json()['access_token']
    graphApiResponse = requests.get(graphUsersUrl, headers={
                                    "Authorization": 'Bearer ' + token, "Accept": 'application/json'})
    graphApi = graphApiResponse.json()
    for group in graphApi["value"]:
        if group["displayName"] == 'Admins':
            return True
    return False


def confirm_order(email, order_id, config):
    functionUrl = f'https://{config.domain}.azurewebsites.net/api/HttpTrigger?code={config.key}'
    functionBody = {
        "email": email,
        "order_id": order_id
    }
    response = requests.post(functionUrl, functionBody)
    print(response)
    return response.status_code == 200

def return_insights_script(insight_key):
    return """
            !function(T,l,y){var S=T.location,k='script',D='instrumentationKey',C='ingestionendpoint',I='disableExceptionTracking',E='ai.device.',b='toLowerCase',w='crossOrigin',N='POST',e='appInsightsSDK',t=y.name||'appInsights';(y.name||T[e])&&(T[e]=t);var n=T[t]||function(d){var g=!1,f=!1,m={initialize:!0,queue:[],sv:'5',version:2,config:d};function v(e,t){var n={},a='Browser';return n[E+'id']=a[b](),n[E+'type']=a,n['ai.operation.name']=S&&S.pathname||'_unknown_',n['ai.internal.sdkVersion']='javascript:snippet_'+(m.sv||m.version),{time:function(){var e=new Date;function t(e){var t=''+e;return 1===t.length&&(t='0'+t),t}return e.getUTCFullYear()+'-'+t(1+e.getUTCMonth())+'-'+t(e.getUTCDate())+'T'+t(e.getUTCHours())+':'+t(e.getUTCMinutes())+':'+t(e.getUTCSeconds())+'.'+((e.getUTCMilliseconds()/1e3).toFixed(3)+'').slice(2,5)+'Z'}(),iKey:e,name:'Microsoft.ApplicationInsights.'+e.replace(/-/g,'')+'.'+t,sampleRate:100,tags:n,data:{baseData:{ver:2}}}}var h=d.url||y.src;if(h){function a(e){var t,n,a,i,r,o,s,c,u,p,l;g=!0,m.queue=[],f||(f=!0,t=h,s=function(){var e={},t=d.connectionString;if(t)for(var n=t.split(';'),a=0;a<n.length;a++){var i=n[a].split('=');2===i.length&&(e[i[0][b]()]=i[1])}if(!e[C]){var r=e.endpointsuffix,o=r?e.location:null;e[C]='https://'+(o?o+'.':'')+'dc.'+(r||'services.visualstudio.com')}return e}(),c=s[D]||d[D]||'',u=s[C],p=u?u+'/v2/track':d.endpointUrl,(l=[]).push((n='SDK LOAD Failure: Failed to load Application Insights SDK script (See stack for details)',a=t,i=p,(o=(r=v(c,'Exception')).data).baseType='ExceptionData',o.baseData.exceptions=[{typeName:'SDKLoadFailed',message:n.replace(/\./g,'-'),hasFullStack:!1,stack:n+'\nSnippet failed to load ['+a+'] -- Telemetry is disabled\nHelp Link: https://go.microsoft.com/fwlink/?linkid=2128109\nHost: '+(S&&S.pathname||'_unknown_')+'\nEndpoint: '+i,parsedStack:[]}],r)),l.push(function(e,t,n,a){var i=v(c,'Message'),r=i.data;r.baseType='MessageData';var o=r.baseData;return o.message='AI (Internal): 99 message:''+('SDK LOAD Failure: Failed to load Application Insights SDK script (See stack for details) ('+n+')').replace(/\'/g,'')+''',o.properties={endpoint:a},i}(0,0,t,p)),function(e,t){if(JSON){var n=T.fetch;if(n&&!y.useXhr)n(t,{method:N,body:JSON.stringify(e),mode:'cors'});else if(XMLHttpRequest){var a=new XMLHttpRequest;a.open(N,t),a.setRequestHeader('Content-type','application/json'),a.send(JSON.stringify(e))}}}(l,p))}function i(e,t){f||setTimeout(function(){!t&&m.core||a()},500)}var e=function(){var n=l.createElement(k);n.src=h;var e=y[w];return!e&&''!==e||'undefined'==n[w]||(n[w]=e),n.onload=i,n.onerror=a,n.onreadystatechange=function(e,t){'loaded'!==n.readyState&&'complete'!==n.readyState||i(0,t)},n}();y.ld<0?l.getElementsByTagName('head')[0].appendChild(e):setTimeout(function(){l.getElementsByTagName(k)[0].parentNode.appendChild(e)},y.ld||0)}try{m.cookie=l.cookie}catch(p){}function t(e){for(;e.length;)!function(t){m[t]=function(){var e=arguments;g||m.queue.push(function(){m[t].apply(m,e)})}}(e.pop())}var n='track',r='TrackPage',o='TrackEvent';t([n+'Event',n+'PageView',n+'Exception',n+'Trace',n+'DependencyData',n+'Metric',n+'PageViewPerformance','start'+r,'stop'+r,'start'+o,'stop'+o,'addTelemetryInitializer','setAuthenticatedUserContext','clearAuthenticatedUserContext','flush']),m.SeverityLevel={Verbose:0,Information:1,Warning:2,Error:3,Critical:4};var s=(d.extensionConfig||{}).ApplicationInsightsAnalytics||{};if(!0!==d[I]&&!0!==s[I]){var c='onerror';t(['_'+c]);var u=T[c];T[c]=function(e,t,n,a,i){var r=u&&u(e,t,n,a,i);return!0!==r&&m['_'+c]({message:e,url:t,lineNumber:n,columnNumber:a,error:i}),r},d.autoExceptionInstrumented=!0}return m}(y.cfg);function a(){y.onInit&&y.onInit(n)}(T[t]=n).queue&&0===n.queue.length?(n.queue.push(a),n.trackPageView({})):a()}(window,document,{
            src: 'https://js.monitor.azure.com/scripts/b/ai.2.min.js', // The SDK URL Source
            // name: 'appInsights', // Global SDK Instance name defaults to 'appInsights' when not supplied
            // ld: 0, // Defines the load delay (in ms) before attempting to load the sdk. -1 = block page load and add to head. (default) = 0ms load after timeout,
            // useXhr: 1, // Use XHR instead of fetch to report failures (if available),
            crossOrigin: 'anonymous', // When supplied this will add the provided value as the cross origin attribute on the script tag
            // onInit: null, // Once the application insights instance has loaded and initialized this callback function will be called with 1 argument -- the sdk instance (DO NOT ADD anything to the sdk.queue -- as they won't get called)
            cfg: { // Application Insights Configuration 
            instrumentationKey: '""" +  insight_key + """'
            }});"""