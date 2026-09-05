# Privacy design

VoxVision AI starts only after the user clicks **Start Analysis**. The extension visibly reports microphone, screen, backend, and paused status. It stores transcript text, OCR text, user-marked context, and final reports only.

Audio recordings, video recordings, screenshots, image blobs, and canvas frame data are never persisted. A selected screen is held in memory only long enough to detect changes and submit an OCR request; the backend processes that image in memory and stores its extracted text instead of the image.

AI keys stay in the backend `.env` file. The extension never contains keys. Microphone transcription is explicitly identified as Web Speech API transcription and may not capture remote attendees. Sharing a tab with audio does not change that limitation.
