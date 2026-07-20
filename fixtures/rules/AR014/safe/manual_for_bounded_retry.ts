interface UploadClient {
  upload(path: string): void;
}

function uploadWithRetry(client: UploadClient, path: string): void {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      client.upload(path);
      break;
    } catch (err) {
      continue;
    }
  }
}
