def transcribe(client, audio_file):
    return client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        timeout=30,
    )
