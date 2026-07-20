const axios = require("axios");

function fetchStatus(dispatchId) {
  return axios.get(`https://api.example.com/dispatch/${dispatchId}`, { timeout: 5000 });
}
