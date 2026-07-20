function uploadWithRetry(client, path) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      client.upload(path);
      break;
    } catch (err) {
      continue;
    }
  }
}
