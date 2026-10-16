# QR Code Generator

A full-stack QR code generator with a dark-themed browser UI and a Python FastAPI backend.

## Features

| Mode | Description |
|---|---|
| **Standard** | Colored QR codes with custom foreground/background and module size |
| **With Logo** | QR code with a logo image overlaid in the center |
| **Animated** | QR code embedded onto an animated GIF background |

## Project Structure

```
.
├── index.html      # Frontend UI (vanilla JS + Tailwind CSS)
├── styles.css      # Custom component styles
├── bknd.py         # FastAPI backend (API + static file server)
└── qrengine.py     # QR generation engine (qrcode + segno + Pillow)
```

## Setup

### 1. Install dependencies

```bash
pip install fastapi uvicorn qrcode[pil] Pillow segno python-multipart
```

### 2. Run the server

```bash
python bknd.py
```

Or with uvicorn directly:

```bash
uvicorn bknd:app --reload --host 127.0.0.1 --port 8000
```

### 3. Open in browser

Navigate to **http://127.0.0.1:8000**

The backend serves `index.html` at `/`, so no separate web server is needed.

## API Reference

All endpoints accept `multipart/form-data` POST requests.

### `POST /api/qr/standard`
| Field | Type | Default | Description |
|---|---|---|---|
| `data` | string | required | Text or URL to encode |
| `fill_color` | string | `#000000` | QR module color (hex) |
| `back_color` | string | `#ffffff` | Background color (hex) |
| `box_size` | int | `10` | Pixels per module (1–50) |
| `border` | int | `4` | Border width in modules (0–10) |

Returns: `image/png`

### `POST /api/qr/logo`
| Field | Type | Default | Description |
|---|---|---|---|
| `data` | string | required | Text or URL to encode |
| `fill_color` | string | `#000000` | QR module color (hex) |
| `back_color` | string | `#ffffff` | Background color (hex) |
| `box_size` | int | `10` | Pixels per module |
| `logo` | file | required | Logo image (PNG/JPG) |

Returns: `image/png`

### `POST /api/qr/animated`
| Field | Type | Default | Description |
|---|---|---|---|
| `data` | string | required | Text or URL to encode |
| `gif` | file | required | Background GIF |
| `scale` | int | `8` | QR scale factor (2–20) |

Returns: `image/gif`
