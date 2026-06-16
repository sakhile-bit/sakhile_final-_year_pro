# Injection Security Checks — Pre-Deployment Security Gate

**Added to:** `src/gui/screens/deployment_screen.py` → `CodeSecurityChecker`  
**Check IDs:** CCS-04 (HTML Injection / XSS) · CCS-05 (JavaScript Injection)  
**Severity:** CRITICAL  
**Category:** code  
**Total checks after addition:** 23 (was 21)

---

## Overview

Two new static-analysis checks were added to the Pre-Deployment Security Gate to detect **HTML injection (XSS)** and **JavaScript injection** vulnerabilities before code ships to users. Both checks scan source files for dangerous patterns without executing any code.

---

## CCS-04 — HTML Injection / XSS

### What it checks

Scans all source files (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.php`, `.rb`, `.go`, `.java`, `.cs`) for patterns where user-supplied data is rendered directly into HTML output without sanitisation.

### Patterns detected

| Pattern | Language | Risk |
|---------|----------|------|
| `\| safe` filter in templates | Python / Jinja2 | Marks user data as trusted HTML — bypasses auto-escaping |
| `Markup(variable)` | Python / Flask | Wraps dynamic content as raw HTML |
| `echo $_GET[...]` / `echo $_POST[...]` | PHP | Prints superglobal input directly into output |
| `print $_REQUEST[...]` / `$_COOKIE` / `$_SERVER` | PHP | Same — any PHP superglobal echo |
| `element.innerHTML = variable` | HTML / JS | Inserts raw HTML from a variable |
| `element.outerHTML = variable` | HTML / JS | Replaces element with raw HTML |
| `document.write(variable)` | JavaScript | Writes arbitrary content to the DOM |
| `raw(params...)` / `.html_safe` on params | Ruby on Rails | Bypasses Rails HTML escaping on user input |
| `getWriter().write(request.getParameter(...))` | Java Servlets | Writes request parameter directly to HTTP response |

### Example — flagged code

```python
# FLAGGED: |safe passes raw user input to HTML
return render_template_string("<p>{{ comment|safe }}</p>", comment=user_input)

# FLAGGED: Markup() on a variable
return Markup(user_input)
```

```php
<?php
// FLAGGED: echo with superglobal
echo $_GET['name'];
print $_POST['comment'];
?>
```

```js
// FLAGGED: innerHTML with variable
document.getElementById('output').innerHTML = userData;
document.write(apiResponse);
```

### Example — safe code (not flagged)

```python
# SAFE: auto-escaped template
return render_template('page.html', name=user_input)

# SAFE: Markup on a literal string only
return Markup("<b>Welcome</b>")
```

```js
// SAFE: textContent never parses HTML
document.getElementById('output').textContent = userData;
```

### Remediation

- Use template engine **auto-escaping** (Jinja2, Twig, ERB all escape by default — do not disable it).
- Replace `innerHTML` with `textContent` when inserting plain text.
- Use **DOMPurify** to sanitise HTML before inserting it via `innerHTML`.
- In PHP, wrap all output with `htmlspecialchars($var, ENT_QUOTES, 'UTF-8')`.
- Never use `Markup()` or `|safe` on any value that originates from user input, a database, or an API.

---

## CCS-05 — JavaScript Injection

### What it checks

Scans **JavaScript and TypeScript files only** (`.js`, `.ts`, `.jsx`, `.tsx`) for patterns that allow arbitrary script execution or DOM-based XSS.

### Patterns detected

| Pattern | Risk |
|---------|------|
| `eval(variable)` | Executes an arbitrary string as JavaScript |
| `new Function(...)` | Constructs and executes a function from a string |
| `setTimeout("string", ...)` / `setInterval("string", ...)` | Executes a string as code after a delay |
| `element.innerHTML = variable` | Inserts raw HTML — can execute `<script>` or event handlers |
| `element.outerHTML = variable` | Same risk as `innerHTML` |
| `$(...).html(variable)` | jQuery unsafe HTML insertion |
| `document.write(variable)` | Writes arbitrary content to the document |
| `insertAdjacentHTML(...)` | Parses and inserts HTML adjacent to an element |
| `location.href = variable` / `window.location = variable` | Open redirect — can redirect to `javascript:` URI |

### Example — flagged code

```js
// FLAGGED: eval with variable
eval(userCode);

// FLAGGED: new Function from string
const fn = new Function('return ' + userInput);

// FLAGGED: setTimeout with string argument
setTimeout("alert('xss')", 1000);

// FLAGGED: innerHTML with variable
document.getElementById('box').innerHTML = serverResponse;

// FLAGGED: insertAdjacentHTML
el.insertAdjacentHTML('beforeend', userContent);

// FLAGGED: open redirect
window.location = userSuppliedUrl;

// FLAGGED: jQuery .html() with variable
$('#output').html(apiData);
```

### Example — safe code (not flagged)

```js
// SAFE: textContent — never executes HTML
document.getElementById('box').textContent = userData;

// SAFE: JSON.parse instead of eval
const obj = JSON.parse(serverData);

// SAFE: setTimeout with a function reference
setTimeout(() => doWork(), 1000);
setTimeout(doWork, 500);

// SAFE: innerHTML reset to empty literal
el.innerHTML = '';
```

### Remediation

- Replace `eval()` with `JSON.parse()` for data parsing, or a proper parser for other use cases.
- Replace `innerHTML` with `textContent` for plain text; use **DOMPurify** when HTML is required.
- Pass a **function reference** (not a string) to `setTimeout` / `setInterval`.
- Avoid `new Function()` — if dynamic execution is genuinely needed, use a sandboxed `iframe` or a Worker.
- Validate and whitelist redirect URLs before assigning to `location.href`.
- Use `insertAdjacentText()` instead of `insertAdjacentHTML()` for plain text.

---

## Check IDs — full revised catalogue

| ID | Name | Severity | Checks for |
|----|------|----------|------------|
| CCS-01 | Non-HTTPS URLs | MEDIUM | Hardcoded `http://` in source files |
| CCS-02 | SQL Injection Patterns | CRITICAL | f-string / format SQL queries |
| CCS-03 | Command Injection Risk | CRITICAL | `shell=True`, `eval()`, `os.system()` |
| **CCS-04** | **HTML Injection / XSS** | **CRITICAL** | **Unsanitised user input in HTML output** |
| **CCS-05** | **JavaScript Injection** | **CRITICAL** | **Dangerous JS execution patterns** |
| CCS-06 | Backup / Temp Files | LOW | `.bak`, `.tmp`, `dump.sql` in project tree |
| CCS-07 | Pinned Dependencies | HIGH | Unpinned versions in `requirements.txt` |
| CCS-08 | Exception Handling | MEDIUM | Silent `except: pass` handlers |

---

## Scan runner integration

Both checks are called inside `DeploymentCheckerScreen._run_scan()` as part of the **code scanning** phase:

```python
code_checks_labeled = [
    (code_checker._check_hardcoded_http_urls,    "Code: Non-HTTPS URLs…"),
    (code_checker._check_sql_injection_patterns, "Code: SQL injection patterns…"),
    (code_checker._check_command_injection,      "Code: Command injection…"),
    (code_checker._check_html_injection,         "Code: HTML injection / XSS…"),   # NEW
    (code_checker._check_js_injection,           "Code: JavaScript injection…"),   # NEW
    (code_checker._check_backup_temp_files,      "Code: Backup/temp files…"),
    (code_checker._check_requirements_pinned,    "Code: Dependency manifests…"),
    (code_checker._check_broad_exception_handlers, "Code: Exception handling…"),
]
```

A **CRITICAL** failure in either check sets the deployment verdict to **BLOCKED**, preventing deployment until the issues are resolved.

---

## False-positive guidance

| Situation | Action |
|-----------|--------|
| `\| safe` used only on server-generated constants | Verify the value never originates from user input, then accept the finding |
| `innerHTML` used with a sanitised value (e.g. DOMPurify output) | Add a comment explaining the sanitisation; the check is pattern-based and will still flag it |
| `eval()` in a test file or build script | Move test/build files outside the scanned source tree, or add the directory to `CodeSecurityChecker.SKIP_DIRS` |
| Legacy PHP codebase with many `echo $_GET` instances | Resolve each one — this is a genuine critical risk |

---

## References

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP DOM-Based XSS](https://owasp.org/www-community/attacks/DOM_Based_XSS)
- [DOMPurify](https://github.com/cure53/DOMPurify) — client-side HTML sanitiser
- CIS Controls v8 — Control 16: Application Software Security
- NIST SP 800-53 SI-10: Information Input Validation
