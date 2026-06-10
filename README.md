#  Quote Builder for Electrical

A Windows desktop application for electrical contractors to build job estimates, generate professional customer quotes as PDFs, track clients, and manage job records from start to completion.

Built with Python, customtkinter, and ReportLab.

> **License:** Source code is available for reference and personal use only.  
> Redistribution or commercial use of this software or its compiled binaries is prohibited without written permission. See [LICENSE](LICENSE) for details.

---

## 📄 Example Quote PDF

Here's what an example quote would look like, which has the ability to be exported via PDF. 

![Quote Preview](example_quote.pdf)

[View Example Quote PDF](example_quote.pdf)

---

## Features

- **New Quote** — Search and add materials from a pre-loaded price list, enter labor hours, miles driven, and markup. Everything calculates in real time.
- **Estimates Log** — Browse all saved estimates and export any as a customer-facing PDF.
- **Client Log** — Store and manage repeat customer info. Auto-fills when building a new quote.
- **Job Log** — Create a job record when work starts, link it to an estimate, and fill in the actual cost and end date when the job is complete.
- **Materials Manager** — Add, edit prices, or remove items from the master price list.
- **PDF Export** — Generates a clean, professional quote showing materials, labor, and fees — no internal markup details visible to the customer.

---

## Screenshots

> *WIP*

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.10+ |
| UI Framework | customtkinter |
| PDF Generation | ReportLab |
| Storage | JSON (local flat files) |
| Distribution | PyInstaller (.exe) |

---

## Running from Source

### 1. Clone the repo
```
git clone https://github.com/regan10444/electric-quote-builder
cd electric-quote-builder
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run
```
python app.py
```

The `data/` folder is created automatically on first run and stores all your estimates, clients, jobs, and materials locally.

---


## Project Structure

```
electric-quote-builder/
├── app.py              ← main application + all UI screens
├── data.py             ← data manager (load/save JSON)
├── quote_pdf.py        ← PDF generation (ReportLab)
├── build.spec          ← PyInstaller build config
├── requirements.txt    ← Python dependencies
├── example_quote.pdf   ← sample output PDF
├── LICENSE             ← usage restrictions
└── README.md
```

---

## About

Built by [Regan Cunningham](https://github.com/regan10444) and Andrew Miclette as a real-world desktop productivity tool.  
Part of a portfolio of practical Python applications targeting small business automation.

---

## License

© Regan Cunningham. All rights reserved.  
See [LICENSE](LICENSE) for full terms. Commercial use requires written permission.
