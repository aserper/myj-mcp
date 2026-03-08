# My J MCP Server

MCP server for the JCC of Greater Boston (Leventhal-Sidman JCC) mobile app, built by reverse-engineering the [uPace](https://upaceapp.com) platform API from the Android APK (`com.upace.erjcc`).

## Features

24 tools covering everything available in the mobile app:

**Classes & Events** — list, reserve, cancel, favorite, search
**Equipment** — babysitting (JCare), private offices, pickleball courts
**Appointments** — personal training, basketball lessons, swimming lessons
**Waitlist** — view position, join, leave
**Reservations** — view your own + family member reservations
**Info** — facility details, alerts, other programs, video content, feedback

## Install & Run

### uvx (recommended)

```bash
uvx myj-mcp
```

### uv

```bash
uv venv && uv pip install -e .
python -m myj_mcp
```

### Docker

```bash
docker run --rm -e UPACE_EMAIL="you@email.com" -e UPACE_PASSWORD="pass" \
  ghcr.io/aserper/myj-mcp:latest
```

## Configuration

Set credentials via environment variables:

```bash
export UPACE_EMAIL="your@email.com"
export UPACE_PASSWORD="yourpassword"
```

### Claude Code

```json
{
  "mcpServers": {
    "myj": {
      "command": "uvx",
      "args": ["myj-mcp"],
      "env": {
        "UPACE_EMAIL": "your@email.com",
        "UPACE_PASSWORD": "yourpassword"
      }
    }
  }
}
```

Or with Docker:

```json
{
  "mcpServers": {
    "myj": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/aserper/myj-mcp:latest"],
      "env": {
        "UPACE_EMAIL": "your@email.com",
        "UPACE_PASSWORD": "yourpassword"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `login` | Authenticate with email/password |
| `list_classes` | List classes by date (default: today) |
| `list_events` | List events by date |
| `reserve_class` | Book a class or event |
| `cancel_reservation` | Cancel a reservation or leave waitlist |
| `my_reservations` | View current reservations |
| `family_reservations` | View family member reservations |
| `list_equipment` | List bookable equipment (babysitting, offices) |
| `reserve_equipment` | Book equipment with time slot + duration |
| `list_pt_sessions` | List appointment/PT session types |
| `get_session_times` | Get available times for a session |
| `book_session` | Book a PT/appointment session |
| `get_waitlist` | View waitlisted classes |
| `delete_waitlist` | Leave a waitlist |
| `toggle_favorite` | Add/remove class from favorites |
| `search` | Search classes, equipment, programs |
| `alerts` | View notifications |
| `mark_alert_read` | Mark alert as read |
| `facility_info` | JCC facility information |
| `user_info` | User profile info |
| `other_programs` | Other programs and custom links |
| `video_categories` | Video content categories |
| `video_listings` | Video listings by category |
| `submit_feedback` | Rate a class/event/equipment (1-5) |

## Testing

```bash
uv pip install pytest
pytest tests/ -v
```

## API

Two API versions discovered in the APK:

- **V1** `https://www.upaceapp.com/Api` — form-encoded, auth via `api_key` + `uid` + `user_id`
- **V2** `https://upace.app/api` — Bearer JWT tokens

See [api-discovery.md](api-discovery.md) for full endpoint documentation.

## Project Structure

```
src/myj_mcp/
├── __init__.py
├── __main__.py   # Entry point
├── client.py     # UpaceClient — HTTP client with auth
├── models.py     # Pydantic models
└── server.py     # FastMCP server (24 tools)
```
