interface UploadClient {
  upload(path: string): void;
}

function uploadWithRetry(client: UploadClient, path: string): void {
  while (true) {
    try {
      client.upload(path);
      break;
    } catch (err) {
      continue;
    }
  }
}
