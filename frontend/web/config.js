/**
 * PresenterAI — Configuration
 * Environment-aware settings for the frontend application
 */
(function() {
  const PROD_API = 'https://presentation-api-558900038680.asia-south1.run.app';
  const GOOGLE_CLIENT_ID = '558900038680-el19rsd3kn7gn73h80foe2770fok9bfe.apps.googleusercontent.com';

  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

  window.APP_CONFIG = {
    API_URL: isLocal ? 'http://localhost:8000' : PROD_API,
    GOOGLE_CLIENT_ID: GOOGLE_CLIENT_ID,
    ENV: isLocal ? 'development' : 'production'
  };
})();
