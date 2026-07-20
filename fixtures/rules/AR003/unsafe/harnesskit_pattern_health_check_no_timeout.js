// Inspired by (not copied from) a real HarnessKit shape: a health-check call to a locally-running
// external service, with no timeout -- if the service hangs, the check itself hangs forever.
const axios = require("axios");

function checkServiceHealth(serviceUrl) {
  return axios.get(`${serviceUrl}/health`);
}
