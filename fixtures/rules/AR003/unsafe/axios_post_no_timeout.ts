import axios from "axios";

interface Order {
  amount: number;
}

function submitPayment(order: Order): Promise<unknown> {
  return axios.post("https://payments.example.com/charge", order);
}
