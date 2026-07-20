const axios = require("axios");

function submitPayment(client, order) {
  return axios.post("https://payments.example.com/charge", order);
}
