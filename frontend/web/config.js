(function() {
  // Inject backend URL from deployment
  window.BACKEND_URL = 'https://presentation-api-558900038680.asia-south1.run.app';

  // Prefer the current production OAuth client ID over stale localStorage values.
  const PRODUCTION_GOOGLE_CLIENT_ID = '558900038680-el19rsd3kn7gn73h80foe2770fok9bfe.apps.googleusercontent.com';
  window.GOOGLE_CLIENT_ID = window.GOOGLE_CLIENT_ID || PRODUCTION_GOOGLE_CLIENT_ID || localStorage.getItem('googleClientId');

  // Fallback logic if window.BACKEND_URL not set
  if (!window.BACKEND_URL || window.BACKEND_URL === 'null') {
    // Try to auto-detect for development
    if (window.location.hostname === 'localhost') {
      window.BACKEND_URL = 'http://localhost:8000';
    } else {
      window.BACKEND_URL = 'https://presentation-api-558900038680.asia-south1.run.app';
    }
  }

  // Store in localStorage for persistence
  localStorage.setItem('backendUrl', window.BACKEND_URL);
  localStorage.setItem('googleClientId', window.GOOGLE_CLIENT_ID);
  console.log('Backend URL configured:', window.BACKEND_URL);
})();
