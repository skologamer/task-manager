(async function(){
  if(typeof window === 'undefined') return;
  async function initPush(){
    try{
      const { PushNotifications } = window.Capacitor ? window.Capacitor.Plugins || {} : {};
      if(!PushNotifications){
        console.log('PushNotifications plugin not available (running in browser).');
        return;
      }
      const perm = await PushNotifications.requestPermissions();
      if(perm.receive !== 'granted'){
        console.warn('Push permission not granted');
        return;
      }
      await PushNotifications.register();
      PushNotifications.addListener('registration', (token) => {
        console.log('Push registration success, token: ', token.value);
        try{
          fetch(API_BASE_URL + '/register_token', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ token: token.value, platform: 'capacitor' })
          }).then(r=>console.log('registered token on server', r.status)).catch(e=>console.warn(e));
        }catch(e){ console.warn('register token failed', e); }
      });
      PushNotifications.addListener('registrationError', (err) => {
        console.error('Push registration error', err);
      });
      PushNotifications.addListener('pushNotificationReceived', (notification) => {
        console.log('Push received', notification);
      });
      PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
        console.log('Push action', action);
      });
    }catch(e){
      console.warn('initPush error', e);
    }
  }
  window.initPush = initPush;
})();
