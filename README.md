# SteamSeparator

A lightweight, modern utility to automatically organize your Steam library into quality collections based on real user reviews and an adaptive Bayesian confidence filter.

**SteamSeparator** writes directly to Steam's native collection format (`cloud-storage-namespace-1.json`) to create clean, reliable rating categories.

---

## ⚠️ Important Context & Disclaimer

Before you dive in, there are three important things you should know:

1. **Vibecoded with AI**:  
   I vibecoded this entire application using an AI assistant (Google DeepMind's Antigravity). Since I didn't write the underlying code line-by-line myself, I **cannot take personal responsibility** for bugs, edge cases, or unforeseen behavior. Use it at your own discretion — though the tool does create automatic, timestamped backups of your collection files before touching anything!

2. **Not a Depressurizer Replacement (Not Even Close)**:  
   Legacy tools like *Depressurizer* were Swiss Army knives packed with dozens of features: organizing by tags, genres, completion times (HLTB), release years, and a million other parameters.  
   **SteamSeparator is not that.** It does exactly **one thing and one thing only**: it groups your library into quality collections based solely on **Steam user ratings backed by a Bayesian confidence filter**. That is the only feature I personally needed, and that is all this app does.

3. **Feature Requests & Maintenance**:  
   You are very welcome to open issues or share ideas! However, please understand that I cannot guarantee whether or when a request can be implemented, as I am dependent on Antigravity to build, debug, and maintain this codebase. PRs from fellow developers are, of course, always welcome!

---

## Features

- **Clean Game Detection**:
  - Automatically filters out DLCs, dedicated servers, betas, soundtracks, test depots, and tools.
  - Resolves true game titles and crisp store banners via public Steam store metadata.

- **Statistical Bayesian Quality Filter**:
  - A game with 10 out of 10 positive reviews is not an all-time classic; it simply has a small sample size.
  - The Bayesian filter weights review percentages against total review counts. High-rated games with broad player consensus qualify for top tiers, while low-confidence titles remain excluded rather than falsely downgraded.

- **3 Strictness Presets**:
  - **Low**: Tolerant (~800 reviews needed for top tiers).
  - **Medium** *(Default)*: Balanced (~1,900 reviews needed).
  - **High**: Strict (~3,800 reviews needed).

- **Safety & Integrity**:
  - Automatic timestamped backup created before any changes are written.
  - Existing user collections (e.g., *Favorites*, *Backlog*, *Completed*) remain completely untouched.
  - Verifies that the Steam client is closed before applying changes to prevent Steam Cloud overwrite conflicts.

- **Privacy-First & 100% Local**:
  - **No login credentials or Steam API keys required.**
  - All communication is local; reviews are queried anonymously from public Steam store endpoints.
  - Fast local SQLite cache (`ratings.db`) so subsequent launches load in under a second.

- **Bilingual Interface**:
  - Seamless toggle between English and German in the header.

---

## Quick Start

### Prerequisites
- Python 3.10 or newer
- Steam installed locally

### Installation & Launch

1. Clone or download this repository:
   ```bash
   git clone https://github.com/<your-username>/SteamSeparator.git
   cd SteamSeparator
   ```

2. Install the minimal dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```bash
   python run.py
   ```
   *(On Windows, you can also simply double-click `launch.bat`)*

4. Your web browser will automatically open at `http://localhost:8765`.

---

## Usage Guide

1. **Select Account**: Choose your Steam user profile from the dropdown in the header.
2. **Scan Reviews**: Click **"Scan Reviews"** to fetch current review data for your library games.
3. **Tune & Preview**:
   - Choose your Review Filter preset (*Low*, *Medium*, or *High*).
   - Select which collections you want created in Steam (e.g. *Overwhelmingly Positive*, *Very Positive*).
   - Inspect the real-time preview table.
4. **Apply to Steam**:
   - Completely exit the Steam desktop client.
   - Click **"Apply to Steam"**.
   - Restart Steam — your library is now organized!

---

## Contributing & License

Contributions, feature suggestions, and bug reports are welcome! Feel free to open an issue or pull request.

Released under the [MIT License](LICENSE).
