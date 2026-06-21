import argparse
import csv
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urljoin
from zoneinfo import ZoneInfo

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# === 全域設定 (可手動修改) ===
GROUP_ID = 54
OJ_HOMEPAGE = "https://formosa.oj.cs.nycu.edu.tw/"
SUBMISSIONS_PER_PAGE = 100
PAGE_WAIT_SECONDS = 10
LOGIN_WAIT_SECONDS = 30
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR / ".env"
LANGUAGE_EXTENSIONS = {
    "C": ".c",
    "C++": ".cpp",
    "C++11": ".cpp",
    "C++14": ".cpp",
    "C++17": ".cpp",
    "C++20": ".cpp",
    "Python": ".py",
    "Python3": ".py",
    "Java": ".java",
}


def load_env_file(path):
    values = {}
    if not path.exists():
        return values

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if (
                (value.startswith('"') and value.endswith('"'))
                or (value.startswith("'") and value.endswith("'"))
            ):
                value = value[1:-1]
            values[key] = value
    return values


def get_env_value(name, fallback_names=()):
    env_values = load_env_file(ENV_FILE)
    for key in (name, *fallback_names):
        value = os.getenv(key)
        if value:
            return value.strip()
        value = env_values.get(key)
        if value:
            return value.strip()
    return ""


def load_login_credentials():
    username = get_env_value("OJ_USERNAME", ("USERNAME", "OJ_USER", "USER_NAME"))
    password = get_env_value("OJ_PASSWORD", ("PASSWORD", "OJ_PASS"))
    if not username or not password:
        raise RuntimeError(
            f"找不到登入資訊，請在 {ENV_FILE} 設定 OJ_USERNAME 與 OJ_PASSWORD。"
        )
    return username, password


def build_search_url(problem_id, oj_id, page):
    query = urlencode({
        "count": SUBMISSIONS_PER_PAGE,
        "name": oj_id,
        "page": page,
        "problem_id": problem_id,
    })
    return f"{OJ_HOMEPAGE}groups/{GROUP_ID}/submissions/?{query}"


def resolve_url(url):
    return urljoin(OJ_HOMEPAGE, url)


def parse_score(score_text):
    score_text = score_text.strip()
    if score_text.isdigit():
        return int(score_text)

    first_part = score_text.split("/", 1)[0].strip()
    try:
        return int(float(first_part))
    except ValueError:
        return 0


def normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def safe_page_text(page):
    parts = []
    try:
        parts.append(page.title() or "")
    except Exception:
        pass
    try:
        parts.append(page.locator("body").inner_text() or "")
    except Exception:
        pass
    return normalize_text(" ".join(parts))


def page_shows_login_choices(page):
    page_text = safe_page_text(page)
    return ("google" in page_text and "nycu" in page_text) or "choose google" in page_text


def page_shows_login_error(page):
    error_pattern = re.compile(
        r"please check your username or password|check your username or password|"
        r"login info wrong|wrong password|incorrect password|invalid credential",
        re.I,
    )
    try:
        if page.get_by_text(error_pattern).count() > 0:
            return True
    except Exception:
        pass
    page_text = safe_page_text(page)
    return bool(error_pattern.search(page_text))


def login_still_failed(page):
    try:
        if page_shows_login_error(page):
            return True
    except Exception:
        pass

    try:
        if page_shows_login_choices(page):
            return True
    except Exception:
        pass

    try:
        if page.locator("input[type='password']").count() > 0:
            return True
    except Exception:
        pass

    return False


def page_needs_authorization(page):
    page_text = safe_page_text(page)
    return "authorize nctu online judge" in page_text or "authorizing will redirect" in page_text


def click_authorize_button(page):
    candidates = page.locator("button, input[type='submit'], a")
    count = candidates.count()
    for index in range(count):
        item = candidates.nth(index)
        try:
            if not item.is_visible() or not item.is_enabled():
                continue
            text = normalize_text(
                " ".join([
                    item.text_content() or "",
                    item.get_attribute("value") or "",
                    item.get_attribute("aria-label") or "",
                    item.get_attribute("title") or "",
                ])
            )
            if "authorize" in text or "authorize" in text.replace(" ", ""):
                item.click()
                return True
        except Exception:
            continue
    return False


def handle_authorization(page):
    if not page_needs_authorization(page):
        return False

    try:
        page.get_by_role("button", name=re.compile(r"^Authorize$", re.I)).wait_for(
            state="visible",
            timeout=PAGE_WAIT_SECONDS * 1000,
        )
    except Exception:
        pass

    if click_authorize_button(page):
        try:
            page.wait_for_load_state("domcontentloaded", timeout=LOGIN_WAIT_SECONDS * 1000)
        except PlaywrightTimeoutError:
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=LOGIN_WAIT_SECONDS * 1000)
        except PlaywrightTimeoutError:
            pass
        return True

    return False


def click_nycu_oauth_button(page):
    candidates = page.locator("a, button, input[type='button'], input[type='submit']")
    best_index = None
    best_score = 0
    count = candidates.count()

    for index in range(count):
        item = candidates.nth(index)
        try:
            if not item.is_visible() or not item.is_enabled():
                continue
            text = normalize_text(
                " ".join([
                    item.text_content() or "",
                    item.get_attribute("value") or "",
                    item.get_attribute("aria-label") or "",
                    item.get_attribute("title") or "",
                    item.get_attribute("alt") or "",
                    item.get_attribute("id") or "",
                    item.get_attribute("name") or "",
                    item.get_attribute("class") or "",
                    item.get_attribute("href") or "",
                    item.get_attribute("src") or "",
                ])
            )
        except Exception:
            continue

        if "google" in text:
            continue

        score = 0
        if "nycu" in text:
            score += 10
        if "national yang ming chiao tung university" in text:
            score += 8
        if "yang ming" in text:
            score += 4
        if "oauth" in text or "o auth" in text or "outh" in text:
            score += 2

        if score > best_score:
            best_score = score
            best_index = index

    if best_index is None:
        return False

    candidates.nth(best_index).click()
    return True


def click_submit_button(page, scope=None):
    root = scope if scope is not None else page
    candidates = root.locator("button, input[type='submit'], input[type='button'], a")
    count = candidates.count()
    for index in range(count):
        item = candidates.nth(index)
        try:
            if not item.is_visible() or not item.is_enabled():
                continue
            text = normalize_text(
                " ".join([
                    item.text_content() or "",
                    item.get_attribute("value") or "",
                    item.get_attribute("aria-label") or "",
                    item.get_attribute("title") or "",
                ])
            )
            if any(keyword in text for keyword in ("submit", "login", "log in", "sign in", "登入", "送出", "提交")):
                item.click()
                return True
        except Exception:
            continue
    return False


def pick_username_input(page):
    inputs = page.locator("input")
    best_index = None
    best_score = -1
    count = inputs.count()

    for index in range(count):
        item = inputs.nth(index)
        try:
            input_type = normalize_text(item.get_attribute("type") or "")
            if input_type in {"hidden", "password", "submit", "button", "checkbox", "radio", "file", "image", "reset"}:
                continue

            attributes = normalize_text(" ".join([
                item.get_attribute("name") or "",
                item.get_attribute("id") or "",
                item.get_attribute("placeholder") or "",
                item.get_attribute("aria-label") or "",
                item.get_attribute("autocomplete") or "",
            ]))
        except Exception:
            continue

        score = 0
        for keyword in ("user", "username", "email", "account", "login", "id"):
            if keyword in attributes:
                score += 2
        if input_type in {"text", "email", "tel"}:
            score += 1

        if score > best_score:
            best_score = score
            best_index = index

    if best_index is None:
        return None
    return inputs.nth(best_index)


def login_oj(page, max_attempts=3):
    username, password = load_login_credentials()

    for attempt in range(1, max_attempts + 1):
        page.goto(OJ_HOMEPAGE, wait_until="domcontentloaded")

        if not click_nycu_oauth_button(page):
            page.get_by_text("NYCU", exact=False).click(timeout=PAGE_WAIT_SECONDS * 1000)

        try:
            page.locator("input[type='password']").first.wait_for(state="visible", timeout=PAGE_WAIT_SECONDS * 1000)
        except PlaywrightTimeoutError:
            time.sleep(1)
            if not click_nycu_oauth_button(page):
                raise RuntimeError("找不到 NYCU OAuth 按鈕，無法進行自動登入。")
            page.locator("input[type='password']").first.wait_for(state="visible", timeout=PAGE_WAIT_SECONDS * 1000)

        password_input = page.locator("input[type='password']").first
        username_input = pick_username_input(page)
        if username_input is None:
            raise RuntimeError("找不到帳號輸入欄位，無法自動登入。")

        username_input.fill(username)
        password_input.fill(password)

        try:
            password_input.press("Tab")
        except Exception:
            pass

        time.sleep(1)

        login_form = None
        try:
            login_form = password_input.locator("xpath=ancestor::form[1]")
            if login_form.count() == 0:
                login_form = None
            else:
                login_form = login_form.first
        except Exception:
            login_form = None

        submitted = False
        if login_form is not None:
            submitted = click_submit_button(page, scope=login_form)
            if not submitted:
                try:
                    login_form.evaluate("form => form.submit()")
                    submitted = True
                except Exception:
                    pass

        if not submitted:
            submitted = click_submit_button(page)

        if not submitted:
            try:
                password_input.press("Enter")
                submitted = True
            except Exception:
                pass

        login_deadline = time.time() + LOGIN_WAIT_SECONDS
        while time.time() < login_deadline:
            if handle_authorization(page):
                continue
            if not login_still_failed(page):
                break
            if page_shows_login_error(page):
                break
            page.wait_for_timeout(500)

        if login_still_failed(page):
            print(f"登入失敗，第 {attempt} 次嘗試：偵測到帳密錯誤訊息。")
            if attempt == max_attempts:
                break
            time.sleep(1)
            continue

        page.goto(OJ_HOMEPAGE, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=LOGIN_WAIT_SECONDS * 1000)
        except PlaywrightTimeoutError:
            pass
        if not login_still_failed(page):
            return

        if attempt < max_attempts:
            time.sleep(1)

    raise RuntimeError("登入失敗，已達 3 次嘗試上限，請確認 NYCU 帳密是否正確。")


def wait_for_rows(page):
    row_locators = [
        page.locator("tbody[data-radium='true'] > tr"),
        page.locator("table tbody > tr"),
        page.locator("tbody > tr"),
    ]

    try:
        page.wait_for_function(
            """
            () => {
                const bodyText = document.body ? document.body.innerText : '';
                const rowCount = document.querySelectorAll('tbody tr').length;
                return rowCount > 0 || /No Match Submission/i.test(bodyText);
            }
            """,
            timeout=PAGE_WAIT_SECONDS * 4000,
        )
    except PlaywrightTimeoutError:
        raise PlaywrightTimeoutError("submission rows did not render in time")

    body_text = normalize_text(page.locator("body").inner_text())
    if "no match submission" in body_text:
        return []

    for rows in row_locators:
        try:
            if rows.count() > 0:
                return rows.element_handles()
        except Exception:
            continue

    raise PlaywrightTimeoutError("submission rows did not render in time")


def load_submission_rows(page, url, max_attempts=3):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=PAGE_WAIT_SECONDS * 2000)
            except PlaywrightTimeoutError:
                pass
            return wait_for_rows(page)
        except PlaywrightTimeoutError as e:
            last_error = e
            if attempt < max_attempts:
                page.wait_for_timeout(1000)
                continue
            raise

    if last_error is not None:
        raise last_error
    raise PlaywrightTimeoutError("submission rows did not render in time")


def wait_for_submission_detail(page):
    page.wait_for_load_state("domcontentloaded", timeout=PAGE_WAIT_SECONDS * 1000)
    candidates = page.locator("[data-clipboard-text], pre, code, textarea")
    try:
        candidates.first.wait_for(state="visible", timeout=PAGE_WAIT_SECONDS * 1000)
        return
    except PlaywrightTimeoutError:
        pass

    page.wait_for_timeout(1000)
    candidates.first.wait_for(state="attached", timeout=PAGE_WAIT_SECONDS * 1000)


def is_no_match(row_handles):
    if len(row_handles) != 1:
        return False
    return normalize_text(row_handles[0].inner_text()) == "no match submission"


def extract_language(page):
    table_cells = page.locator("table th, table td")
    cell_texts = [normalize_text(table_cells.nth(i).inner_text()) for i in range(table_cells.count())]
    cell_texts = [text for text in cell_texts if text]

    for text in cell_texts:
        for language in LANGUAGE_EXTENSIONS:
            if text == normalize_text(language):
                return language

    for text in cell_texts:
        for language in LANGUAGE_EXTENSIONS:
            if text.startswith(normalize_text(language)):
                return language

    return ""


def extract_code(page):
    clipboard_elements = page.locator("[data-clipboard-text]")
    clipboard_texts = []
    for index in range(clipboard_elements.count()):
        text = clipboard_elements.nth(index).get_attribute("data-clipboard-text")
        if text and text.strip():
            clipboard_texts.append(text)
    if clipboard_texts:
        return max(clipboard_texts, key=len)

    for selector in ("pre", "code", "textarea"):
        elements = page.locator(selector)
        for index in range(elements.count()):
            item = elements.nth(index)
            code_text = item.input_value() if selector == "textarea" else item.text_content()
            if code_text and code_text.strip():
                return code_text

    return ""


def format_handin_time(target_time, deadline_tz):
    if target_time is None:
        return ""
    return target_time.astimezone(deadline_tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def write_score_row(writer, name, student_id, score, handin_time=""):
    writer.writerow({
        "name": name,
        "student_id": student_id,
        "score": score,
        "handin_time": handin_time,
    })


def main(args):
    problem_id = args.problem_id
    deadline_str = args.deadline
    students_file_path = args.students_file
    deadline_tz = ZoneInfo(args.deadline_tz)
    oj_tz = ZoneInfo(args.oj_tz)

    report_folder = args.report_folder if args.report_folder else f"problem_{problem_id}_report"

    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d_%H:%M:%S").replace(tzinfo=deadline_tz)
    except ValueError:
        print("錯誤：deadline 格式不正確。請使用 'YYYY-MM-DD_HH:MM:SS' 格式。")
        return

    students = []
    try:
        with open(students_file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not all(field in reader.fieldnames for field in ["name", "student_id", "oj_id"]):
                print("錯誤：CSV 檔案缺少必要的欄位。請確保檔案包含 'name', 'student_id', 'oj_id' 這三欄。")
                return
            for row in reader:
                students.append(row)
    except FileNotFoundError:
        print(f"錯誤：找不到學生名單檔案 '{students_file_path}'。請檢查檔案路徑。")
        return
    except Exception as e:
        print(f"讀取 CSV 檔案時發生錯誤: {e}")
        return

    if not os.path.exists(report_folder):
        os.makedirs(report_folder)

    if not os.path.exists(f"{report_folder}/code"):
        os.makedirs(f"{report_folder}/code")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context()
        page = context.new_page()

        try:
            login_oj(page)

            with open(os.path.join(report_folder, "score.csv"), "w", encoding="utf-8-sig", newline="") as score_f:
                score_writer = csv.DictWriter(score_f, fieldnames=["name", "student_id", "score", "handin_time"])
                score_writer.writeheader()

                for student in students:
                    name = student["name"]
                    student_id_num = student["student_id"]
                    oj_id = student["oj_id"]

                    target_score = None
                    target_url = None
                    target_time = None
                    reached_last_page = False

                    for page_num in range(1, args.max_pages + 1):
                        try:
                            rows = load_submission_rows(
                                page,
                                build_search_url(problem_id, oj_id, page_num),
                            )
                        except Exception as e:
                            print(f"[{oj_id}] 無法載入 submission 列表第 {page_num} 頁: {e}")
                            continue

                        if is_no_match(rows):
                            if page_num == 1:
                                print(f"[{oj_id}] 沒有繳交紀錄。")
                            reached_last_page = True
                            break

                        for row in rows:
                            try:
                                time_str = row.query_selector("td:nth-of-type(10)").inner_text().strip()
                                sub_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=oj_tz)
                            except Exception as e:
                                print(f"[{oj_id}] 無法解析時間: {e}")
                                continue

                            if sub_time <= deadline:
                                try:
                                    score_text = row.query_selector("td:nth-of-type(9)").inner_text().strip()
                                    score = parse_score(score_text)
                                    link_element = row.query_selector("td:nth-of-type(1) a")
                                    submission_url = link_element.get_attribute("href")
                                except Exception as e:
                                    print(f"[{oj_id}] 無法解析繳交資料: {e}")
                                    continue

                                if target_score is None or score > target_score:
                                    target_score = score
                                    target_url = submission_url
                                    target_time = sub_time

                        if target_score == 100 or len(rows) < SUBMISSIONS_PER_PAGE:
                            reached_last_page = True
                            break

                    if not reached_last_page:
                        print(f"[{oj_id}] 警告：已掃描 {args.max_pages} 頁，可能還有更早的繳交未檢查。")

                    if target_score is None:
                        print(f"[{oj_id}] 沒有在 deadline 前繳交。")
                        write_score_row(score_writer, name, student_id_num, 0)
                        continue

                    target_time_str = format_handin_time(target_time, deadline_tz)

                    if target_score == 0:
                        print(f"[{oj_id}] deadline 前最高分為0，不下載程式碼。")
                        write_score_row(score_writer, name, student_id_num, 0, target_time_str)
                        continue

                    page.goto(resolve_url(target_url), wait_until="domcontentloaded")
                    try:
                        wait_for_submission_detail(page)
                    except Exception as e:
                        print(f"[{oj_id}] 無法完整載入繳交詳細頁: {e}")

                    language = extract_language(page)
                    if not language:
                        print(f"[{oj_id}] 無法找到程式語言。")

                    ext = LANGUAGE_EXTENSIONS.get(language, ".txt")

                    code_text = extract_code(page)
                    if not code_text:
                        print(f"[{oj_id}] 找不到程式碼按鈕。")
                        write_score_row(score_writer, name, student_id_num, target_score, target_time_str)
                        continue

                    filename = f"{name}_{student_id_num}{ext}"
                    save_path = os.path.join(report_folder, "code", filename)

                    with open(save_path, "w", encoding="utf-8", newline="") as f:
                        f.write(code_text)

                    print(f"[{oj_id}] 已下載程式碼 -> {save_path} (語言: {language}, 分數: {target_score}, 繳交: {target_time_str})")
                    write_score_row(score_writer, name, student_id_num, target_score, target_time_str)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="自動從 Formosa OJ 下載指定問題的學生程式碼。")
    parser.add_argument("--problem-id", type=int, required=True, help="目標問題的 ID (必填)")
    parser.add_argument("--deadline", type=str, required=True, help="繳交截止時間 (必填)，格式為 'YYYY-MM-DD_HH:MM:SS'")
    parser.add_argument("--report-folder", type=str, help="儲存報告和程式碼的資料夾名稱 (選填，預設為 'problem_{problem_id}_report')")
    parser.add_argument("--students-file", type=str, default="students.csv", help="學生名單檔案路徑 (選填，預設為 'students.csv'，需包含 name, student_id, oj_id 三欄")
    parser.add_argument("--deadline-tz", type=str, default="Asia/Taipei", help="deadline 所使用的時區 (預設: Asia/Taipei)")
    parser.add_argument("--oj-tz", type=str, default="Asia/Taipei", help="OJ 繳交時間顯示所使用的時區 (預設: Asia/Taipei)")
    parser.add_argument("--max-pages", type=int, default=20, help="每位學生最多掃描的 submissions 頁數 (預設: 20)")
    parser.add_argument("--headed", action="store_true", help="以可視模式啟動瀏覽器，而不是背景執行")

    args = parser.parse_args()
    main(args)
    print("Done")
