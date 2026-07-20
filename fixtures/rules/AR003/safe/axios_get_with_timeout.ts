import axios from "axios";

function fetchStatus(dispatchId: string): Promise<unknown> {
  return axios.get(`https://api.example.com/dispatch/${dispatchId}`, { timeout: 5000 });
}
