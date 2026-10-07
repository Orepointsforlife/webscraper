import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import webbrowser
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class SeleniumScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("Selenium web scraper ")
        self.root.geometry("1280x720")
        self.root.resizable(True, True)

        self.target_url = ""
        self.search_results = []
        self.driver = None

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self.root,
            text="Selenium JavaScript-Enabled Scraper",
            font=("Arial", 22, "bold"),
            pady=15,
            fg="#1565c0"
        )
        title_label.pack()

        info_label = tk.Label(
            self.root,
            text="✨ Uses Selenium to execute JavaScript and scrape dynamic content",
            font=("Arial", 9, "italic"),
            fg="#43a047"
        )
        info_label.pack()

        # URL Frame
        url_frame = tk.LabelFrame(self.root, text="Target URL", font=("Arial", 11, "bold"), padx=10, pady=10)
        url_frame.pack(fill="x", padx=20, pady=10)

        self.url_entry = tk.Entry(url_frame, font=("Arial", 11), width=70)
        self.url_entry.insert(0, self.target_url)
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.scrape_btn = tk.Button(
            url_frame,
            text="🚀 SCRAPE WITH SELENIUM",
            command=self.scrape_page,
            bg="#1976d2",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=25,
            pady=8
        )
        self.scrape_btn.pack(side="left", padx=10)

        # Options frame
        options_frame = tk.Frame(url_frame)
        options_frame.pack(side="left", padx=10)

        self.headless_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options_frame,
            text="Headless (no browser window)",
            variable=self.headless_var,
            font=("Arial", 9)
        ).pack()

        self.wait_time_var = tk.IntVar(value=0)
        wait_frame = tk.Frame(options_frame)
        wait_frame.pack()
        tk.Label(wait_frame, text="Wait time (sec):", font=("Arial", 8)).pack(side="left")
        tk.Spinbox(wait_frame, from_=0, to=20, textvariable=self.wait_time_var, width=5, font=("Arial", 8)).pack(
            side="left", padx=2)

        # Debug output
        debug_frame = tk.LabelFrame(self.root, text="Page Source & Console Output", font=("Arial", 10, "bold"), padx=5,
                                    pady=5)
        debug_frame.pack(fill="both", expand=False, padx=20, pady=5)

        self.debug_text = scrolledtext.ScrolledText(debug_frame, font=("Consolas", 8), height=10, wrap=tk.WORD,
                                                    bg="#f5f5f5")
        self.debug_text.pack(fill="both", expand=True)

        # Results Frame
        results_frame = tk.LabelFrame(self.root, text="Extracted Videos & Media", font=("Arial", 11, "bold"), padx=5,
                                      pady=5)
        results_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # Treeview
        tree_container = tk.Frame(results_frame)
        tree_container.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal")

        self.results_tree = ttk.Treeview(
            tree_container,
            columns=("Type", "Text", "URL"),
            show="tree headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        v_scrollbar.config(command=self.results_tree.yview)
        h_scrollbar.config(command=self.results_tree.xview)

        self.results_tree.heading("#0", text="No.")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Text", text="Title/Description")
        self.results_tree.heading("URL", text="URL")

        self.results_tree.column("#0", width=50, minwidth=50)
        self.results_tree.column("Type", width=180, minwidth=120)
        self.results_tree.column("Text", width=450, minwidth=200)
        self.results_tree.column("URL", width=500, minwidth=200)

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Action buttons
        action_frame = tk.Frame(self.root, pady=10)
        action_frame.pack(fill="x", padx=20)

        self.open_btn = tk.Button(
            action_frame,
            text="🌐 Open Selected",
            command=self.open_selected,
            bg="#ff6f00",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            state="disabled"
        )
        self.open_btn.pack(side="left", padx=10)

        self.copy_btn = tk.Button(
            action_frame,
            text="📋 Copy URL",
            command=self.copy_url,
            bg="#2e7d32",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            state="disabled"
        )
        self.copy_btn.pack(side="left", padx=10)

        self.download_btn = tk.Button(
            action_frame,
            text="💾 Download Video",
            command=self.download_video,
            bg="#7b1fa2",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            state="disabled"
        )
        self.download_btn.pack(side="left", padx=10)

        tk.Button(
            action_frame,
            text="🗑️ Clear",
            command=self.clear_results,
            bg="#616161",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15
        ).pack(side="right", padx=10)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Enter URL and click SCRAPE WITH SELENIUM")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            font=("Arial", 10),
            bg="#e0e0e0",
            pady=5
        )
        status_bar.pack(side="bottom", fill="x")

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")

    def scrape_page(self):
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showwarning("URL Required", "Please enter a URL to scrape.")
            return

        self.clear_results()
        self.scrape_btn.config(state="disabled")
        self.status_var.set("Starting Selenium browser... Please wait")
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.start(10)

        # Run in thread
        thread = threading.Thread(target=self.scrape_with_selenium, args=(url,))
        thread.daemon = True
        thread.start()

    def scrape_with_selenium(self, url):
        try:
            self.root.after(0, lambda: self.status_var.set("Initializing Chrome driver..."))

            # Setup Chrome options
            chrome_options = Options()
            if self.headless_var.get():
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)

            self.root.after(0, lambda: self.status_var.set(f"Loading page: {url}"))

            # Load page
            self.driver.get(url)

            # Wait for JavaScript to load
            wait_time = self.wait_time_var.get()
            self.root.after(0, lambda: self.status_var.set(f"Waiting {wait_time}s for JavaScript to execute..."))
            time.sleep(wait_time)

            # Additional wait for dynamic content
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass

            self.root.after(0, lambda: self.status_var.set("Extracting content..."))

            # Get page source after JavaScript execution
            page_source = self.driver.page_source

            # Show debug info
            preview = page_source[:3000]
            self.root.after(0, lambda: self.debug_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.debug_text.insert("1.0", preview + "\n\n[...truncated...]"))

            soup = BeautifulSoup(page_source, 'html.parser')
            results = []

            # Strategy 1: Find all video elements
            videos = self.driver.find_elements(By.TAG_NAME, "video")
            for video in videos:
                try:
                    src = video.get_attribute('src')
                    if not src:
                        sources = video.find_elements(By.TAG_NAME, "source")
                        if sources:
                            src = sources[0].get_attribute('src')

                    if src:
                        results.append({
                            'type': '🎬 VIDEO ELEMENT',
                            'text': video.get_attribute('title') or '[Direct Video]',
                            'url': src
                        })
                except:
                    pass

            # Strategy 2: Find all iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    src = iframe.get_attribute('src')
                    if src:
                        results.append({
                            'type': '📺 IFRAME',
                            'text': iframe.get_attribute('title') or '[Embedded Content]',
                            'url': src
                        })

                        # Try to switch to iframe and scrape inside
                        try:
                            self.driver.switch_to.frame(iframe)

                            # Look for videos inside iframe
                            iframe_videos = self.driver.find_elements(By.TAG_NAME, "video")
                            for vid in iframe_videos:
                                vid_src = vid.get_attribute('src')
                                if not vid_src:
                                    sources = vid.find_elements(By.TAG_NAME, "source")
                                    if sources:
                                        vid_src = sources[0].get_attribute('src')
                                if vid_src:
                                    results.append({
                                        'type': '🎥 VIDEO IN IFRAME',
                                        'text': '[From embedded iframe]',
                                        'url': vid_src
                                    })

                            # Switch back to main content
                            self.driver.switch_to.default_content()
                        except:
                            self.driver.switch_to.default_content()
                except:
                    pass

            # Strategy 3: Find all links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.text

                    if href:
                        link_type = "🔗 Link"

                        # Check for video files
                        if any(ext in href.lower() for ext in ['.mp4', '.webm', '.avi', '.mkv', '.m3u8', '.mpd']):
                            link_type = "🎬 DIRECT VIDEO FILE"
                        elif any(kw in href.lower() for kw in ['video', 'watch', 'play']):
                            link_type = "🎥 Video Link"

                        if link_type != "🔗 Link" or (text and len(text.strip()) > 0):
                            results.append({
                                'type': link_type,
                                'text': text[:200] if text else '[No text]',
                                'url': href
                            })
                except:
                    pass

            # Strategy 4: Execute JavaScript to find video URLs
            try:
                # Try to find video URLs in JavaScript variables
                js_videos = self.driver.execute_script("""
                    let videos = [];

                    // Check all video elements
                    document.querySelectorAll('video').forEach(v => {
                        if (v.src) videos.push(v.src);
                        v.querySelectorAll('source').forEach(s => {
                            if (s.src) videos.push(s.src);
                        });
                    });

                    // Check for common video player variables
                    if (typeof videoUrl !== 'undefined') videos.push(videoUrl);
                    if (typeof video_url !== 'undefined') videos.push(video_url);
                    if (typeof playerConfig !== 'undefined' && playerConfig.file) videos.push(playerConfig.file);

                    return videos;
                """)

                for vid_url in js_videos:
                    if vid_url:
                        results.append({
                            'type': '⚡ JS EXTRACTED VIDEO',
                            'text': '[Found via JavaScript execution]',
                            'url': vid_url
                        })
            except:
                pass

            # Strategy 5: Look in page source for video URLs with regex
            video_url_patterns = [
                r'https?://[^\s"\'<>]+\.(?:mp4|webm|m3u8|mpd)',
                r'"file":\s*"([^"]+)"',
                r'"source":\s*"([^"]+\.(?:mp4|webm))"',
            ]

            for pattern in video_url_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    video_url = match if isinstance(match, str) else match[0]
                    if video_url and any(ext in video_url for ext in ['.mp4', '.webm', '.m3u8', '.mpd']):
                        results.append({
                            'type': '🔍 REGEX FOUND VIDEO',
                            'text': '[Extracted from page source]',
                            'url': video_url
                        })

            # Remove duplicates
            seen_urls = set()
            unique_results = []
            for r in results:
                if r['url'] not in seen_urls:
                    seen_urls.add(r['url'])
                    unique_results.append(r)

            self.search_results = unique_results
            self.root.after(0, self.display_results)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error",
                                                            f"Selenium scraping failed:\n{str(e)}\n\nMake sure Chrome and ChromeDriver are installed."))
            self.root.after(0, self.scrape_complete)
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def display_results(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.scrape_btn.config(state="normal")

        if not self.search_results:
            self.status_var.set("No videos found")
            messagebox.showinfo("No Results", "No videos or media found on this page.")
            return

        # Prioritize video content
        video_results = [r for r in self.search_results if any(x in r['type'] for x in ['VIDEO', 'IFRAME'])]
        other_results = [r for r in self.search_results if not any(x in r['type'] for x in ['VIDEO', 'IFRAME'])]
        sorted_results = video_results + other_results

        for i, result in enumerate(sorted_results, 1):
            self.results_tree.insert(
                "",
                "end",
                text=str(i),
                values=(
                    result['type'],
                    result['text'][:100] + "..." if len(result['text']) > 100 else result['text'],
                    result['url']
                ),
                tags=('video',) if 'VIDEO' in result['type'] else ()
            )

        # Highlight video rows
        self.results_tree.tag_configure('video', background='#e8f5e9')

        self.open_btn.config(state="normal")
        self.copy_btn.config(state="normal")
        self.download_btn.config(state="normal")
        self.status_var.set(f"Found {len(self.search_results)} items ({len(video_results)} videos)")

    def scrape_complete(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.scrape_btn.config(state="normal")

    def open_selected(self):
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to open.")
            return

        item = self.results_tree.item(selection[0])
        url = item['values'][2]
        webbrowser.open(url)
        self.status_var.set(f"Opened: {url}")

    def copy_url(self):
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item.")
            return

        item = self.results_tree.item(selection[0])
        url = item['values'][2]

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.status_var.set("URL copied to clipboard!")
        except:
            messagebox.showerror("Error", "Could not copy to clipboard")

    def download_video(self):
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video to download.")
            return

        item = self.results_tree.item(selection[0])
        url = item['values'][2]

        # Try to download the video
        try:
            self.status_var.set("Downloading video...")
            response = requests.get(url, stream=True, timeout=30)

            if response.status_code == 200:
                # Get filename from URL
                filename = url.split('/')[-1].split('?')[0]
                if not any(ext in filename for ext in ['.mp4', '.webm', '.avi']):
                    filename += '.mp4'

                from tkinter import filedialog
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".mp4",
                    initialfile=filename,
                    filetypes=[("Video files", "*.mp4 *.webm *.avi"), ("All files", "*.*")]
                )

                if save_path:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    self.status_var.set(f"Downloaded: {save_path}")
                    messagebox.showinfo("Success", f"Video downloaded to:\n{save_path}")
            else:
                messagebox.showerror("Error", f"Failed to download. Status code: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Download Error", f"Could not download video:\n{str(e)}")

    def clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.search_results = []
        self.debug_text.delete("1.0", tk.END)
        self.open_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.download_btn.config(state="disabled")
        self.status_var.set("Results cleared")


if __name__ == "__main__":
    root = tk.Tk()
    app = SeleniumScraper(root)
    root.mainloop()