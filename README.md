# YouTube Video Downloader and Info API

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Description
The YouTube Video Downloader and Info API is a Flask-based Python project that allows you to download YouTube videos and retrieve video information using PytubeFix. It now includes a browser frontend where you can paste a link, load available resolutions, and download a merged MP4 with audio directly to your machine.

1. **Download Video:** You can specify the video URL and resolution to download YouTube videos directly to your local machine.

2. **Get Video Info:** You can retrieve detailed information about a YouTube video, including its title, author, length, views, description, and publish date.

This project is designed to simplify the process of interacting with YouTube content programmatically.

## Features
- Browser frontend for downloading videos from a link.
- Resolution picker with common presets and dynamic resolution loading.
- Automatic merge of video-only and audio-only streams when needed.
- Download YouTube videos in various resolutions.
- Retrieve comprehensive information about YouTube videos.
- Error handling for reliable performance.
- JSON API endpoints for easy integration into other applications.

## Libraries and Technologies Used
- Python 3.x
- Flask for building the API and frontend.
- PytubeFix for interacting with YouTube content.
- FFmpeg for merging audio and video streams.
- re and urllib.parse for URL validation.

## Usage
1. Clone this repository: `git clone https://github.com/zararashraf/youtube-video-downloader-api.git`
2. Install the required libraries: `pip install flask pytubefix`
3. Run the Flask application: `python main.py`
4. Open the browser frontend at `http://127.0.0.1:5000/`
5. Or access the API endpoints using HTTP requests (for example in Postman).

## Deploying Online
The project is deploy-ready with Docker and Gunicorn. The Docker image installs FFmpeg automatically, so video + audio merging works in production.

### Railway Deployment
1. Push this repository to GitHub.
2. Create a new Railway project and connect the GitHub repository.
3. Railway will detect `railway.toml` and/or the `Dockerfile`.
4. Deploy using the Docker build.
5. Open the generated Railway URL.

Railway environment variables:
- `PORT` is provided automatically by Railway.
- No extra Python variables are required for the default setup.

### Local Docker Test
```bash
docker build -t youtube-downloader .
docker run --rm -p 8000:8000 youtube-downloader
```

Then open `http://127.0.0.1:8000/`.

### Notes
- The `downloads/` folder is ignored from Git and is treated as runtime storage.
- If you want downloaded files to persist on Railway, attach a persistent volume. Otherwise they may disappear after redeploys or restarts.
- The frontend is served from Flask, so you do not need a separate frontend hosting service.

## API Endpoints

### Download Video by Resolution
- **Endpoint:** `/download/<resolution>`
- **HTTP Method:** POST
- **Request Body:** JSON
    ```json
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    ```

### Download Video File in Browser
- **Endpoint:** `/download_file/<resolution>`
- **HTTP Method:** POST or GET
- **Behavior:** Returns the final MP4 file as a browser download.
- **Example:** `POST /download_file/720p` with JSON body containing the URL.

### Get Video Info
- **Endpoint:** `/video_info`
- **HTTP Method:** POST
- **Request Body:** JSON
    ```json
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    ```

### Get Available Resolutions
- **Endpoint:** `/available_resolutions`
- **HTTP Method:** POST
- **Request Body:** JSON
    ```json
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    ```

## Frontend Usage
1. Paste a YouTube link into the page.
2. Click **Load resolutions** to fetch the available options for that video.
3. Choose a resolution such as `720p` or `1080p`.
4. Click **Download video** to receive the merged MP4 in your browser download folder.

## Screenshots
### Downloading a Video
![image](https://github.com/zararashraf/youtube-video-downloader-api/assets/36181292/edad60c8-27fc-4ed0-8243-21ffc4cc16cc)

### Retrieving Info
![image](https://github.com/zararashraf/youtube-video-downloader-api/assets/36181292/e0e3aeb3-fa97-41c7-9d89-971f2cda421e)


## Code Repository
You can access the source code for this project on [GitHub](https://github.com/zararashraf/youtube-video-downloader-api/blob/main/main.py).

## License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT). You are free to use, modify, and distribute the code while providing appropriate attribution.
