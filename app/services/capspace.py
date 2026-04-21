"""Capspace reconciliation automations — Unit Register, Loan Register, Interest Payments.

Pure functions lifted verbatim from the Streamlit source
(Handover_automations/Capspace/Capspace-PDF-Extractor-Automations/app.py) with
Streamlit calls dropped. `uploaded_file` args have been swapped for
`file_bytes` / `filename` so the service is framework-agnostic.

UNIT_MASTER and LOAN_MASTER are hardcoded dicts — known tech debt, not to be
fixed during migration (per CLAUDE.md).
"""
from __future__ import annotations

import datetime
import io
import math

import pandas as pd
import xlsxwriter


# ═══════════════════════════════════════════════════════════════════════════════
# ── UNIT REGISTER CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
UNIT_FUND_CODES = ["CDLOT2", "CPDF", "DLOT", "CDLOT"]
UNIT_SUFFIXES = [
    "Superannuation Fund", "Superannunation Fund", "Supperannuation Fund",
    "Superannuation", "Superannunation", "Supperannuation",
    "Trust Fund", "Family Trust", "Trust", "Fund",
]
UNIT_MASTER = {
    "John Barnett Nominees Pty Ltd ATF JGB Superannunation Fund": "John Barnett Nominees Pty Ltd ATF JGB Superannuation Fund",
    "Hunter Brunelle Nominees Pty Ltd RS Hunter Supperannuation Fund": "Hunter Brunelle Nominees Pty Ltd RS Hunter Superannuation Fund",
    "IT Contracting Services Pty Ltd ATF Zabow Supperannuation Fund": "IT Contracting Services Pty Ltd ATF Zabow Superannuation Fund",
    "Adorben Pty Limited ATF Adorben Pty Limited Supperannuation Fund": "Adorben Pty Limited ATF Adorben Pty Limited",
    "Kaufline Superannuation Pty Ltd ATF Kaufline Family": "Kaufline Superannuation Pty Ltd ATF Kaufline Family Super Fund",
    "BDH Superannuation Fund Pty Ltd ATF BDH Supperannuation Fund": "BDH Superannuation Fund Pty Ltd ATF BDH Superannuation Fund",
    "D2 Enterprises Pty Ltd ATF The Muirhead Supperannuation Fund": "D2 Enterprises Pty Ltd ATF The Muirhead Superannuation Fund",
    "Graymere Pty Limited ATF The Graymere Superannuation Fund": "Graymere Pty Limited ATF The Graymere Superannuation",
    "Loreak Mendian Pty Ltd ATF Telleria Family Trust": "Richard Telleria",
    "Sesame Bagel Pty Ltd ATF Sesame Bagel Trust": "Sesame Bagel Trust",
    "Gandalf Investments Pty Ltd ATF Elliot Rubinstein Supperannuation": "Gandalf Investments Pty Ltd ATF Elliot Rubinstein",
    "Supermann Pty Ltd ATF Cartisano Super Fund": "Supermann Pty Limited ATF Cartisano Superannuation Fund",
    "Abata Pty Ltd ATF Williams Family Trust": "Abata Pty Ltd",
    "Constel Investments Pty Ltd ATF Pavlakos Family Super Fund": "Constel Investments Pty Ltd ATF Pavlakos Family Superannuation F",
}

# ═══════════════════════════════════════════════════════════════════════════════
# ── LOAN REGISTER CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
LOAN_MASTER = {
    "John Richard Hill ABN 13 042 324 991": ("CPDF", "002 - Loan - JR Hill"),
    "Benjamin Christey Ashe Bradley ABN 72 876 275 693": ("CPDF", "003 - Loan - BC Bradley"),
    "Campbell Parade NB Property Pty Ltd ATF Campbell": ("CPDF", "005 - Loan - Campbell Parade NB Property Pty Ltd"),
    "XWB Pty Ltd": ("CPDF", "007 - Loan - XWB Pty Ltd"),
    "P.J. Wilson & Co ABN 96 301 718 068": ("CPDF", "008 - Loan - PJ Wilson"),
    "JAC Investment (NSW) Pty Ltd": ("CPDF", "009 - Loan - JAC Investments Pty Ltd"),
    "Khattar Investment Pty Ltd ATF John St Unit Trust": ("CPDF", "011 - Loan - John Street Unit Trust (Khattar)"),
    "Albert Square NSW Pty Ltd ACN 637 057 991": ("CPDF", "013 - Loan - Albert Square NSW Pty Ltd"),
    "Jonathon Redwood ABN 25 832 335 126": ("CPDF", "014 - Loan - Jonathan Redwood"),
    "Sathio Investments Pty Ltd ATF": ("CPDF", "015 - Loan - Sathio Investments Trust"),
    "Horizon Professional Services Pty Ltd": ("CPDF", "016 - Loan - Horizon Professional Services Pty Ltd"),
    "Artevista Pty Ltd ACN 629 756 869 ATF Artevista Trust": ("CPDF", "017 - Loan - Artevista Pty Ltd"),
    "T.H.E. Project 151222 Pty Ltd": ("CPDF", "018 - Loan - THE Project 151222 Pty Ltd"),
    "Beluga Finance Pty Ltd": ("CPDF", "020 - Loan - Beluga Finance Pty Ltd"),
    "Libra Investment Group Pty Ltd": ("CPDF", "021 - Loan - Libra Investment Group Pty Ltd"),
    "Richmond Family Business P/L ATF The TR & SJ": ("CPDF", "022 - Loan - Richmond Family Business Pty Ltd"),
    "Wealth Built Right Pty Ltd": ("CPDF", "023 - Loan - Wealth Built Right Pty Ltd"),
    "Chriss Group Pty Ltd": ("CPDF", "024 - Loan - Chriss Group Pty Ltd"),
    "Kymanial P/L ATF Kymanial Settlement and Skermanic": ("CPDF", "025 - Loan - Skerritt Group"),
    "Brookes Family Investments Pty Limited ATF Karibaa": ("CPDF", "026 - Loan - Brookes Karibaa Trust"),
    "FWT Group of Companies": ("CPDF", "027 - Loan - FWT Pty Ltd"),
    "Hub Advisory Pty Ltd": ("CPDF", "028 - Loan - Hub Advisory Pty Ltd"),
    "VIC's Bondi Junction Pty Ltd": ("CPDF", "029 - Loan - Vic's Bondi Junction Pty Ltd"),
    "101 Kingstreet Pty Ltd": ("CPDF", "030 - Loan - 101 King Street Pty Ltd"),
    "CHZ Property Portfolio Pty Ltd ATF The Purple Frog Unit": ("CPDF", "031 - Loan - CHZ Property Portfolio Pty Ltd"),
    "JVS & CS Pty Ltd": ("CPDF", "032 - Loan - JVS & CS Pty Ltd"),
    "TMR Investments Group Pty Ltd": ("CPDF", "033 - Loan - TMR Investments Group Pty Ltd"),
    "Kiloran Pastoral Pty Ltd": ("CPDF", "034 - Loan - Kiloran Pastoral Pty Ltd"),
    "Gray Property Holdings Pty Limited": ("CPDF", "035 - Loan - Gray Property Holdings Pty Ltd"),
    "Telbest Pty Ltd ATF Tino Carusi Family Trust": ("CPDF", "036 - Loan - Telbest Pty Ltd"),
    "Mallinger Projects Pty Ltd": ("CPDF", "037 - Loan - Mallinger Projects Pty Ltd"),
    "World Capital Pty Ltd ATF World Capital Trust": ("CPDF", "038 - Loan - World Capital Pty Ltd"),
    "AAAM Investments (Aust) Pty Ltd ATFT AAAM": ("CPDF", "039 - Loan - AAAM Investments (Aust) Pty Ltd"),
    "Queen & Collins Pty Ltd (Standby)": ("CPDF", "633 - Loan - Queen & Collins Pty Ltd"),
    "Exsupero Pty Ltd ATF Exsupero Trust - Tranche 1": ("CPDF", "640 - Loan - Exsupero Pty Ltd"),
    "First Pacific Capital Pty Ltd": ("CPDF", "643 - Loan - First Pacific Capital Pty Ltd"),
    "Steve and Lams Pty Ltd": ("CPDF", "645 - Loan - Steve and Lams Pty Ltd"),
    "Bella Felicita Pty Ltd": ("CPDF", "646 - Loan - Bella Felicita Pty Ltd"),
    "Whisq Pty Ltd": ("CPDF", "648 - Loan - Whisq Pty Ltd"),
    "Widaki Pty Ltd & Paul Bassett Pty Ltd": ("CPDF", "655 - Loan - Widaki Pty Ltd & Paul Bassett Pty Ltd"),
    "Citi Marketing Pty Ltd": ("CPDF", "656 - Loan - Citi Marketing Pty Ltd"),
    "Crowdy Bay Trust": ("CPDF", "659 - Loan - Crowdy Bay Trust"),
    "Aurora Networks Pty Ltd": ("CPDF", "665 - Loan - Aurora Networks Pty Ltd"),
    "Jofar Pty Ltd": ("CPDF", "667 - Loan - Jofar Pty Ltd"),
    "Area Wealth Administration Services Pty Ltd": ("CPDF", "673 - Loan - Area Wealth Administration Services Pty Ltd"),
    "Helen Lenyszyn Pty Ltd": ("CPDF", "676 - Loan - Helen Lenysyzn Pty Ltd"),
    "Bella Felicita No 2 Pty Ltd": ("CPDF", "678 - Loan - Bella Felicita No 2 Pty Ltd"),
    "Greenfield Resources Australia Pty Ltd": ("CPDF", "681 - Loan - Greenfield Resources Australia Pty Ltd"),
    "Limegrove Administration Pty Ltd ATF The Limegrove": ("CPDF", "683 - Loan - Limegrove Trust"),
    "Mat's Mechanic Pty Ltd": ("CPDF", "689 - Loan - Mat's Mechanic Pty Ltd"),
    "Equisent Developments Pty Ltd": ("CPDF", "690 - Loan - Equisent Developments Pty Ltd"),
    "Ari & May Pty Ltd": ("CPDF", "693 - Loan - Ari & May Pty Ltd"),
    "Tri-Drive Pty Ltd": ("CPDF", "695 - Loan - Tri-Drive Pty Ltd"),
    "98 Dudley Pty Ltd ATF The Dudley Unit Trust": ("CPDF", "696 - Loan - 98 Dudley Pty Ltd"),
    "Templiers Pty Ltd ATF Templiers Trust": ("CPDF", "698 - Loan - Templiers Trust"),
    "A&K Madhoji Pty Ltd ATF The Madjohi Family Trust": ("CPDF", "701 - Loan - The Madhoji Family Trust"),
    "Robyn Bland Pty Ltd": ("CPDF", "707 - Loan - Robyn Bland Pty Ltd"),
    "Hayden Consulting Group Pty Ltd": ("CPDF", "709 - Loan - Hayden Consulting Pty Ltd"),
    "Stump Capital Pty Ltd": ("CPL", "682 - Loan - Stump Capital Pty Ltd"),
    "M Kritikos & A Vloutis": ("CPL", "685 - NCCP Loan - Kritikos & Vloutis"),
    "Gavin & Grainne Mahoney": ("CPL", "686.02 - NCCP Loan - G & G Mahoney - Acc 1013 TMO"),
    "C McLaren & S Blundell": ("CPL", "688 - NCCP - C McLaren & S Blundell"),
    "Maria Karasantes": ("CPL", "690 - NCCP Loan - Maria Karasantes"),
    "Timothy Robert & Samara Jane Richmond": ("CPL", "692 - NCCP Loan - TR & SJ Richmond"),
    "Property Two Enterprises Pty Ltd (Facility B)": ("CDLOT", "631 - Loan - Property Two Enterprises (Facility B)"),
    "Property Two Enterprises Pty Ltd (Facility A)": ("CDLOT", "632 - Loan - Property Two Enterprises (Facility A)"),
    "Good Beer Coronation Pty Ltd": ("CDLOT2", "621 - Loan - Good Beer Coronation Pty Ltd"),
    "A.C.N. 646 685 592 Pty Ltd": ("CPDF", "042 - Loan - ACN 646 685 592 Pty Ltd"),
    "MAPH Property Pty Ltd": ("CPDF", "041 - Loan - MAPH Pty Ltd"),
    "Susan Meryl Ingham ATF SITI Trust": ("CPDF", "043 - Loan - SM Ingham ATF Siti Trust"),
    "Bazinga Enterprises Pty Ltd ATF Sean James Robertson": ("", "054 - Loan - Bazinga Enterprises Pty Ltd"),
    "Betdon Pty Ltd": ("", "052 - Loan - Betdon Pty Ltd"),
    "Health Living Services Group Pty Ltd": ("", "048 - Loan - Health Living Services Group Pty Ltd"),
    "Kingsford Investments Group Pty Ltd ATF B2K Unit Trust": ("", "049 - Loan - Kingsford Investments Group Pty Ltd"),
    "Burley Katon Halliday Pty Ltd": ("", "047 - Loan - Burley Katon Halliday Pty Ltd"),
    "M Boyd Projects Pty Ltd": ("", "046 - Loan - M Boyd Projects Pty Ltd"),
    "Pacific Woods Estate Pty Ltd": ("", "045 - Loan - Pacific Woods Estate Pty Ltd"),
    "1Tap Pty Ltd ATF Penrith Trust": ("", "050 - Loan - 1 Tap Pty Ltd"),
    "26BSL Pty Ltd": ("", "051 - Loan - 26BSL Pty Ltd"),
    "My Beautiful Place Pty Ltd": ("", "053 - Loan - My Beautiful Place Pty Ltd"),
    "Laquinta Palms Pty Ltd ATF Laquinta Palms Trust": ("", "044 - Loan - Laquinta Palms Pty Ltd"),
    "Benibelle Nominees Pty Ltd ATF The Benibelle Family": ("", "056 - Loan - Benibelle Nominees Pty Ltd"),
    "Timothy Jamieson": ("", "057 - Loan - Tim Jamieson"),
    "Option Property Pty Ltd ATF CCSC Property Trust": ("", "058 - Loan - Option Property Pty Ltd"),
    "Alva Capital Pty Ltd": ("", "059 - Loan - Alva Capital Pty Ltd"),
    "Modern Building Development Pty Ltd": ("", "060 - Loan - Modern Building Development Pty Ltd"),
    "Royal Automobile Club of Australia": ("", "061 - Loan - Royal Automobile Club of Australia"),
    "Tanimar Pty Ltd": ("", "062 - Loan - Tanimar Pty Ltd"),
    "Illusion Property No 1 Pty Ltd": ("", "063 - Loan - Illusion Property Pty Ltd"),
    "Egerton Street Holdings ATF Egerton Street Holdings Unit": ("", "064 - Loan - Egerton Street Holdings Unit Trust"),
    "Moondance Nominees Pty Ltd ATF Talle Valley Property": ("", "066 - Loan - Moondance Nominees Pty Ltd"),
    "Flash Auto Pty Ltd ATF The Gortan Family Trust": ("", "065 - Loan - Gortan Family Trust"),
    "44WCP Pty Ltd ATF The Pemulwuy Trust": ("", "068 - Loan - 44WCP Pty Ltd"),
    "Reactive Construction Solutions Pty Ltd": ("", "067 - Loan - Reactive Construction Solutions Pty Ltd"),
    "GWSUV Venture Pty Ltd ATF GWSUV Unit Trust": ("", "069 - Loan - GWSUV Venture Pty Ltd"),
    "M&J (Aust) Pty Ltd ATF The Azzi Family Trust": ("", "070 - Loan - M & J (Aust) Pty Ltd Harrington Childcare"),
    "Est Property Group Pty Ltd  (was Option Property Ltd)": ("", "058 - Loan - Option Property Pty Ltd"),
    "Tango & Cash Investments No 2 Pty Ltd": ("", "071 - Loan - Tango and Cash Property Trust No 2"),
    "P.A.M. Operations Pty Ltd": ("", "072 - Loan - PAM Operations Pty Ltd"),
    "Nomad Nominees Pty Ltd ATF Yazbek Family Trust No. 1": ("", "073 - Loan - Nomad Nominees Pty Ltd"),
    "Elstone Holdings Pty Ltd": ("", "074 - Loan - Elstone Pty Ltd"),
    "Xcenture Pty Ltd": ("", "075 - Loan - Xcenture Pty Ltd"),
    "Redsab Pty Ltd ATF Redsab Unit Trust": ("", "076 - Loan - Redsab Pty Ltd"),
    "25 Chard Road Pty Ltd ATF 25 Chard Rd Property Trust": ("", "077 - Loan - 25 Chard Road Pty Ltd"),
    "Educ8t Pty Ltd": ("", "078 - Loan - Educ8t Pty Ltd"),
    "Geoffrey Hugh Knox ABN 51 455 216 242": ("", "080 - Loan - GH Knox"),
    "Crowdy Bay Eco Retreat Pty Ltd ATF Crowdy Bay Trust": ("", "659 - Loan - Crowdy Bay Trust"),
    "Newcastle Pier Solutions Pty Ltd (was Tri-Drive Pty Ltd)": ("", "695 - Loan - Tri-Drive Pty Ltd"),
    "Casa Maria Pty Ltd ATF Jacques Kurdian Trust": ("", "081 - Loan - Casa Maria Pty Ltd"),
    "Healthy Everyday Pty Ltd ATF Evolve Sanctuary Property": ("", "082 - Loan - Healthy Everyday Pty Ltd"),
    "Moustachar II Pty Ltd": ("", "084 - Loan - Moustachar II Pty Ltd"),
    "Bulletin Accounting Services Pty Ltd ATF Stamford": ("", "083 - Loan - Bulletin Accounting Services Pty Ltd"),
    "11 GS Pty Ltd": ("", "089 - Loan - 11 GS Pty Ltd"),
    "Greenoaks Developments Pty Ltd": ("", "091 - Loan - Greenoaks Developments Pty Ltd"),
    "Zenith Grange Pty Limited  ATF Zenith Grange Unit Trust": ("", "090 - Loan - Zenith Grange Pty Ltd ATF Zenith Grange Unit Trust"),
    "Brosque Football Management Pty Ltd": ("", "094 - Loan - Brosque Football Management Pty Ltd"),
    "Hildarachie Pty Ltd": ("", "093 - Loan - Hildarachie Pty Ltd"),
    "Shockwave Pty Ltd": ("", "095 - Loan - Shockwave Pty Ltd"),
    "RMC Imports And Consulting Pty Ltd": ("", "001 - Loan - RMC Imports & Consulting Pty Ltd"),
    "Betdon Pty Ltd ATF The Giles Family Trust": ("", "052 - Loan - Betdon Pty Ltd"),
    "Aston Holdings Australia Pty Ltd ATF the Armani Group": ("", "Aston Holdings Australia Pty Ltd ATF the Armani Group"),
}

LOAN_MASTER_DATA = [
    ["Entity", "Xero", "Statement"],
    ["CPDF", "002 - Loan - JR Hill", "John Richard Hill ABN 13 042 324 991"],
    ["CPDF", "003 - Loan - BC Bradley", "Benjamin Christey Ashe Bradley ABN 72 876 275 693"],
    ["CPDF", "005 - Loan - Campbell Parade NB Property Pty Ltd", "Campbell Parade NB Property Pty Ltd ATF Campbell "],
    ["CPDF", "007 - Loan - XWB Pty Ltd", "XWB Pty Ltd"],
    ["CPDF", "008 - Loan - PJ Wilson", "P.J. Wilson & Co ABN 96 301 718 068"],
    ["CPDF", "009 - Loan - JAC Investments Pty Ltd", "JAC Investment (NSW) Pty Ltd"],
    ["CPDF", "011 - Loan - John Street Unit Trust (Khattar)", "Khattar Investment Pty Ltd ATF John St Unit Trust"],
    ["CPDF", "013 - Loan - Albert Square NSW Pty Ltd", "Albert Square NSW Pty Ltd ACN 637 057 991"],
    ["CPDF", "014 - Loan - Jonathan Redwood", "Jonathon Redwood ABN 25 832 335 126"],
    ["CPDF", "015 - Loan - Sathio Investments Trust", "Sathio Investments Pty Ltd ATF"],
    ["CPDF", "016 - Loan - Horizon Professional Services Pty Ltd", "Horizon Professional Services Pty Ltd"],
    ["CPDF", "017 - Loan - Artevista Pty Ltd", "Artevista Pty Ltd ACN 629 756 869 ATF Artevista Trust"],
    ["CPDF", "018 - Loan - THE Project 151222 Pty Ltd", "T.H.E. Project 151222 Pty Ltd"],
    ["CPDF", "020 - Loan - Beluga Finance Pty Ltd", "Beluga Finance Pty Ltd"],
    ["CPDF", "021 - Loan - Libra Investment Group Pty Ltd", "Libra Investment Group Pty Ltd"],
    ["CPDF", "022 - Loan - Richmond Family Business Pty Ltd", "Richmond Family Business P/L ATF The TR & SJ "],
    ["CPDF", "023 - Loan - Wealth Built Right Pty Ltd", "Wealth Built Right Pty Ltd"],
    ["CPDF", "024 - Loan - Chriss Group Pty Ltd", "Chriss Group Pty Ltd"],
    ["CPDF", "025 - Loan - Skerritt Group", "Kymanial P/L ATF Kymanial Settlement and Skermanic "],
    ["CPDF", "026 - Loan - Brookes Karibaa Trust", "Brookes Family Investments Pty Limited ATF Karibaa "],
    ["CPDF", "027 - Loan - FWT Pty Ltd", "FWT Group of Companies"],
    ["CPDF", "028 - Loan - Hub Advisory Pty Ltd", "Hub Advisory Pty Ltd"],
    ["CPDF", "029 - Loan - Vic's Bondi Junction Pty Ltd", "VIC's Bondi Junction Pty Ltd"],
    ["CPDF", "030 - Loan - 101 King Street Pty Ltd", "101 Kingstreet Pty Ltd"],
    ["CPDF", "031 - Loan - CHZ Property Portfolio Pty Ltd", "CHZ Property Portfolio Pty Ltd ATF The Purple Frog Unit "],
    ["CPDF", "032 - Loan - JVS & CS Pty Ltd", "JVS & CS Pty Ltd"],
    ["CPDF", "033 - Loan - TMR Investments Group Pty Ltd", "TMR Investments Group Pty Ltd"],
    ["CPDF", "034 - Loan - Kiloran Pastoral Pty Ltd", "Kiloran Pastoral Pty Ltd"],
    ["CPDF", "035 - Loan - Gray Property Holdings Pty Ltd", "Gray Property Holdings Pty Limited"],
    ["CPDF", "036 - Loan - Telbest Pty Ltd", "Telbest Pty Ltd ATF Tino Carusi Family Trust"],
    ["CPDF", "037 - Loan - Mallinger Projects Pty Ltd", "Mallinger Projects Pty Ltd"],
    ["CPDF", "038 - Loan - World Capital Pty Ltd", "World Capital Pty Ltd ATF World Capital Trust"],
    ["CPDF", "039 - Loan - AAAM Investments (Aust) Pty Ltd", "AAAM Investments (Aust) Pty Ltd ATFT AAAM "],
    ["CPDF", "633 - Loan - Queen & Collins Pty Ltd", "Queen & Collins Pty Ltd (Standby)"],
    ["CPDF", "640 - Loan - Exsupero Pty Ltd", "Exsupero Pty Ltd ATF Exsupero Trust - Tranche 1"],
    ["CPDF", "643 - Loan - First Pacific Capital Pty Ltd", "First Pacific Capital Pty Ltd"],
    ["CPDF", "645 - Loan - Steve and Lams Pty Ltd", "Steve and Lams Pty Ltd"],
    ["CPDF", "646 - Loan - Bella Felicita Pty Ltd", "Bella Felicita Pty Ltd"],
    ["CPDF", "648 - Loan - Whisq Pty Ltd", "Whisq Pty Ltd"],
    ["CPDF", "655 - Loan - Widaki Pty Ltd & Paul Bassett Pty Ltd", "Widaki Pty Ltd & Paul Bassett Pty Ltd"],
    ["CPDF", "656 - Loan - Citi Marketing Pty Ltd", "Citi Marketing Pty Ltd"],
    ["CPDF", "659 - Loan - Crowdy Bay Trust", "Crowdy Bay Trust"],
    ["CPDF", "665 - Loan - Aurora Networks Pty Ltd", "Aurora Networks Pty Ltd"],
    ["CPDF", "667 - Loan - Jofar Pty Ltd", "Jofar Pty Ltd"],
    ["CPDF", "673 - Loan - Area Wealth Administration Services Pty Ltd", "Area Wealth Administration Services Pty Ltd"],
    ["CPDF", "676 - Loan - Helen Lenysyzn Pty Ltd", "Helen Lenyszyn Pty Ltd"],
    ["CPDF", "678 - Loan - Bella Felicita No 2 Pty Ltd", "Bella Felicita No 2 Pty Ltd"],
    ["CPDF", "681 - Loan - Greenfield Resources Australia Pty Ltd", "Greenfield Resources Australia Pty Ltd"],
    ["CPDF", "683 - Loan - Limegrove Trust", "Limegrove Administration Pty Ltd ATF The Limegrove "],
    ["CPDF", "689 - Loan - Mat's Mechanic Pty Ltd", "Mat's Mechanic Pty Ltd"],
    ["CPDF", "690 - Loan - Equisent Developments Pty Ltd", "Equisent Developments Pty Ltd"],
    ["CPDF", "693 - Loan - Ari & May Pty Ltd", "Ari & May Pty Ltd"],
    ["CPDF", "695 - Loan - Tri-Drive Pty Ltd", "Tri-Drive Pty Ltd"],
    ["CPDF", "696 - Loan - 98 Dudley Pty Ltd", "98 Dudley Pty Ltd ATF The Dudley Unit Trust"],
    ["CPDF", "698 - Loan - Templiers Trust", "Templiers Pty Ltd ATF Templiers Trust"],
    ["CPDF", "701 - Loan - The Madhoji Family Trust", "A&K Madhoji Pty Ltd ATF The Madjohi Family Trust"],
    ["CPDF", "707 - Loan - Robyn Bland Pty Ltd", "Robyn Bland Pty Ltd"],
    ["CPDF", "709 - Loan - Hayden Consulting Pty Ltd", "Hayden Consulting Group Pty Ltd"],
    ["CPL", "682 - Loan - Stump Capital Pty Ltd", "Stump Capital Pty Ltd"],
    ["CPL", "685 - NCCP Loan - Kritikos & Vloutis", "M Kritikos & A Vloutis"],
    ["CPL", "686.02 - NCCP Loan - G & G Mahoney - Acc 1013 TMO", "Gavin & Grainne Mahoney"],
    ["CPL", "688 - NCCP - C McLaren & S Blundell", "C McLaren & S Blundell"],
    ["CPL", "690 - NCCP Loan - Maria Karasantes", "Maria Karasantes"],
    ["CPL", "692 - NCCP Loan - TR & SJ Richmond", "Timothy Robert & Samara Jane Richmond"],
    ["CDLOT", "631 - Loan - Property Two Enterprises (Facility B)", "Property Two Enterprises Pty Ltd (Facility B)"],
    ["CDLOT", "632 - Loan - Property Two Enterprises (Facility A)", "Property Two Enterprises Pty Ltd (Facility A)"],
    ["CDLOT2", "621 - Loan - Good Beer Coronation Pty Ltd", "Good Beer Coronation Pty Ltd"],
    ["CPDF", "042 - Loan - ACN 646 685 592 Pty Ltd", "A.C.N. 646 685 592 Pty Ltd"],
    ["CPDF", "041 - Loan - MAPH Pty Ltd", "MAPH Property Pty Ltd"],
    ["CPDF", "043 - Loan - SM Ingham ATF Siti Trust", "Susan Meryl Ingham ATF SITI Trust"],
    ["", "054 - Loan - Bazinga Enterprises Pty Ltd", "Bazinga Enterprises Pty Ltd ATF Sean James Robertson"],
    ["", "052 - Loan - Betdon Pty Ltd", "Betdon Pty Ltd"],
    ["", "048 - Loan - Health Living Services Group Pty Ltd", "Health Living Services Group Pty Ltd"],
    ["", "049 - Loan - Kingsford Investments Group Pty Ltd", "Kingsford Investments Group Pty Ltd ATF B2K Unit Trust"],
    ["", "047 - Loan - Burley Katon Halliday Pty Ltd", "Burley Katon Halliday Pty Ltd"],
    ["", "046 - Loan - M Boyd Projects Pty Ltd", "M Boyd Projects Pty Ltd"],
    ["", "045 - Loan - Pacific Woods Estate Pty Ltd", "Pacific Woods Estate Pty Ltd"],
    ["", "050 - Loan - 1 Tap Pty Ltd", "1Tap Pty Ltd ATF Penrith Trust"],
    ["", "051 - Loan - 26BSL Pty Ltd", "26BSL Pty Ltd"],
    ["", "053 - Loan - My Beautiful Place Pty Ltd", "My Beautiful Place Pty Ltd"],
    ["", "044 - Loan - Laquinta Palms Pty Ltd", "Laquinta Palms Pty Ltd ATF Laquinta Palms Trust"],
    ["", "649 - Standby Loan - Inception Asset Management", ""],
    ["", "055 - Loan - Limegrove Trust No 2", "Limegrove Administration Pty Ltd ATF The Limegrove"],
    ["", "056 - Loan - Benibelle Nominees Pty Ltd", "Benibelle Nominees Pty Ltd ATF The Benibelle Family"],
    ["", "057 - Loan - Tim Jamieson", "Timothy Jamieson"],
    ["", "058 - Loan - Option Property Pty Ltd", "Option Property Pty Ltd ATF CCSC Property Trust"],
    ["", "059 - Loan - Alva Capital Pty Ltd", "Alva Capital Pty Ltd"],
    ["", "060 - Loan - Modern Building Development Pty Ltd", "Modern Building Development Pty Ltd"],
    ["", "061 - Loan - Royal Automobile Club of Australia", "Royal Automobile Club of Australia"],
    ["", "062 - Loan - Tanimar Pty Ltd", "Tanimar Pty Ltd"],
    ["", "063 - Loan - Illusion Property Pty Ltd", "Illusion Property No 1 Pty Ltd"],
    ["", "064 - Loan - Egerton Street Holdings Unit Trust", "Egerton Street Holdings ATF Egerton Street Holdings Unit"],
    ["", "066 - Loan - Moondance Nominees Pty Ltd", "Moondance Nominees Pty Ltd ATF Talle Valley Property"],
    ["", "065 - Loan - Gortan Family Trust", "Flash Auto Pty Ltd ATF The Gortan Family Trust"],
    ["", "068 - Loan - 44WCP Pty Ltd", "44WCP Pty Ltd ATF The Pemulwuy Trust"],
    ["", "067 - Loan - Reactive Construction Solutions Pty Ltd", "Reactive Construction Solutions Pty Ltd"],
    ["", "069 - Loan - GWSUV Venture Pty Ltd", "GWSUV Venture Pty Ltd ATF GWSUV Unit Trust"],
    ["", "070 - Loan - M & J (Aust) Pty Ltd Harrington Childcare", "M&J (Aust) Pty Ltd ATF The Azzi Family Trust"],
    ["", "058 - Loan - Option Property Pty Ltd", "Est Property Group Pty Ltd  (was Option Property Ltd)"],
    ["", "071 - Loan - Tango and Cash Property Trust No 2", "Tango & Cash Investments No 2 Pty Ltd"],
    ["", "072 - Loan - PAM Operations Pty Ltd", "P.A.M. Operations Pty Ltd"],
    ["", "073 - Loan - Nomad Nominees Pty Ltd", "Nomad Nominees Pty Ltd ATF Yazbek Family Trust No. 1"],
    ["", "074 - Loan - Elstone Pty Ltd", "Elstone Holdings Pty Ltd"],
    ["", "075 - Loan - Xcenture Pty Ltd", "Xcenture Pty Ltd"],
    ["", "076 - Loan - Redsab Pty Ltd", "Redsab Pty Ltd ATF Redsab Unit Trust"],
    ["", "077 - Loan - 25 Chard Road Pty Ltd", "25 Chard Road Pty Ltd ATF 25 Chard Rd Property Trust"],
    ["", "078 - Loan - Educ8t Pty Ltd", "Educ8t Pty Ltd"],
    ["", "079 - Loan - Sathio Investments Pty Ltd (No 2)", ""],
    ["", "080 - Loan - GH Knox", "Geoffrey Hugh Knox ABN 51 455 216 242"],
    ["", "649 - Standby Loan - Inception Asset Management", ""],
    ["", "659 - Loan - Crowdy Bay Trust", "Crowdy Bay Eco Retreat Pty Ltd ATF Crowdy Bay Trust"],
    ["", "695 - Loan - Tri-Drive Pty Ltd", "Newcastle Pier Solutions Pty Ltd (was Tri-Drive Pty Ltd)"],
    ["", "081 - Loan - Casa Maria Pty Ltd", "Casa Maria Pty Ltd ATF Jacques Kurdian Trust"],
    ["", "082 - Loan - Healthy Everyday Pty Ltd", "Healthy Everyday Pty Ltd ATF Evolve Sanctuary Property"],
    ["", "084 - Loan - Moustachar II Pty Ltd", "Moustachar II Pty Ltd"],
    ["", "083 - Loan - Bulletin Accounting Services Pty Ltd", "Bulletin Accounting Services Pty Ltd ATF Stamford"],
    ["", "087 - Loan - O'Farrell Investment Group Pty Ltd ATF Olja Investment Trust", "O'Farrell Investment Group Pty Ltd ATF Olja Investment"],
    ["", "089 - Loan - 11 GS Pty Ltd", "11 GS Pty Ltd"],
    ["", "091 - Loan - Greenoaks Developments Pty Ltd", "Greenoaks Developments Pty Ltd"],
    ["", "090 - Loan - Zenith Grange Pty Ltd ATF Zenith Grange Unit Trust", "Zenith Grange Pty Limited  ATF Zenith Grange Unit Trust"],
    ["", "", "Organica NSW Pty Ltd ATF Organica NSW Trust"],
    ["", "094 - Loan - Brosque Football Management Pty Ltd", "Brosque Football Management Pty Ltd"],
    ["", "093 - Loan - Hildarachie Pty Ltd", "Hildarachie Pty Ltd"],
    ["", "095 - Loan - Shockwave Pty Ltd", "Shockwave Pty Ltd"],
    ["", "001 - Loan - RMC Imports & Consulting Pty Ltd", "RMC Imports And Consulting Pty Ltd"],
    ["", "052 - Loan - Betdon Pty Ltd", "Betdon Pty Ltd ATF The Giles Family Trust"],
]

# ═══════════════════════════════════════════════════════════════════════════════
# ── INTEREST PAYMENTS CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
INTEREST_PAYEE_LIST = [
    '5114 Pty Ltd', 'Adam Ritson', 'AGVJ Family Trust',
    'AKR Investments (NSW) Pty Ltd ATF The Andrew Rennie Family Trust',
    'Allicante Pty Ltd ATF Shannan Whitney Superannuation Fund',
    'Amagis Family Super Fund', 'Amagis Family Trust', 'Anica Holgate',
    'Barry Verinder', 'Biset Holdings Pty Ltd ATF Kelf & Tactum Superannuation Fund',
    'Blue Arcadia Pty Ltd', 'Blue Pac Super Pty Ltd ATF Blue Pac Superannuation Fund',
    'Carol James', 'D & E Dusevic', 'Darling Pty Ltd ATF Darling Super Fund',
    'David Charles Macourt', 'DCRM No.2 Super Fund', 'Dean Gardiner', 'Encina Trust',
    'Expertiy Capital II AT', 'Fletcher #2 Family Trust', 'Florio Investments',
    'G & R Musico Services Pty Ltd ATF G & R Musico Super Fund',
    'Gatcorp Super Fund Pty Ltd ATF Gatcorp Superannuation Fund', 'Gianna Swadling',
    'Giuseppe & Rosemary Musico', 'Giuseppe Musico', 'H & G Alameddine Family Trust',
    'Hunter Brunelle Nominees Pty Ltd RS Hunter Superannunation Fund',
    'IT Contracting Services Pty Ltd ATF Zabow Superannuation Fund',
    'J & M Chan Pty Ltd ATF Chan Family Pension Fund',
    'JELPSS Pty Ltd ATF Bernie Family Trust',
    'JELPSS Pty Ltd ATF Bernie Family Trust No 2 Account', 'Jennifer Lugsdin',
    'John Barnett Nominees Pty Ltd ATF JGB Superannunation Fund', 'Julian Ludowici',
    'Julio Labraga', 'Katie Andrews', 'Katy Andrews',
    'KEB Nominees Pty Ltd ATF KEB Pension Fund', 'Keith Family Super Fund',
    'Khameleon Enterprises Pty Ltd ATF Renaud Super Fund', 'KN REYNOLDS FAMILY PTY LTD',
    'Lavin Trust', 'Leva Super Pty Ltd ATF Leva Superannuation Fund', 'Locaputo Super Fund',
    'Lynne Bissett', 'M & K Macourt Family Trust', 'Macourt Children Settlement',
    'Macourt Family Pty Ltd ATF Macourt Family Foundation',
    'Magda Macourt Pty Ltd ATF Megda & Kristina Macourt Family Trust',
    'Manujan Pty Ltd ATF Manujan Trust', 'Marigold Pennefather', 'Marlhan Family Trust',
    'Melissa Ball', 'MLM Legacy PL ATF MLM Family Legacy Trust', 'MWLD Super Fund',
    'Natcomp Technology Australia Superannuation Fund', 'Nicholas Lazaridis',
    'Nicole Dunn', 'Nomad Nominees Pty Ltd ATF Ray Superannuation Fund',
    'Paul Dunn', 'Paul Swann', 'PDV Holding Pty Ltd',
    'Petrevski & Co Pty Ltd ATF Petrevski Super Fund', 'Reynolds Family Trust',
    'Sally Skoufis Pty Ltd ATF Sally Skoufis Trust', 'Salvatore Roppolo',
    'Selina Swadling', 'Shannan Whitney', 'Shannan Whitney Super Fund', 'Silvana Koren',
    'Stevenson Computer Services Staff Superannuation Fund', 'Stuart McKinlay',
    'Sura Kandirian (Interest)', 'The Holgate Trust', 'Thrumster One Pty Ltd',
    'The Verinder Superannuation Fund', 'Viano Corporation Pty Ltd',
    'Viano Corporation Pty Ltd account no. 2', 'Viano Corporation Pty Ltd DLOT',
    'Vincent & Laurette Refalo', 'W & CE Stevenson', 'Wilfort Pty Ltd',
    'YDNA Super Pty Ltd ATF Andy & Karen Super fund', 'Jersey Lane Trust',
    'Predad Pty Ltd ATF W J Smith Superannuation Fund', 'S Nav Pty Ltd',
    'The Verinder Family Trust', 'Adorben Superannuation Fund', 'BDH Superannuation Fund',
    'Kaufline Family Super Fund', 'S Nav Pty Ltd DLOT', 'Navarra Enterprises Pty Ltd',
    'Blue Street Finance Pty Ltd', '4th Floor Office Pty Ltd ATF 4th Floor Trust',
    'Grant Pudig', 'Winyard Superannuation Fund', 'Dr Zita Ballok', 'Janet Cecilie Smith',
    'John and Kerrie Barnett', 'Dovile Fraser', 'Eleanor Spano', 'Richard Telleria',
    'Yartvest Pty Ltd', 'Edward Cassidy', 'Longroup Investments Pty Ltd',
    'TY OZ PTY LTD ATF TY OZ Trust', 'Danae No.1 Family Trust',
    'ACN 161 604 315 Pty Ltd', 'Charlotte Taylor',
]

INTEREST_PAGE_BREAK_SIGNALS = ['Powered by The Mortgage Office', 'MORTGAGE POOL DISTRIBUTION AUDIT REPORT']


# ═══════════════════════════════════════════════════════════════════════════════
# ── HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def cv(v):
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s == "nan" else s


def detect_unit_entity(filename: str) -> str:
    name = filename.upper()
    for code in UNIT_FUND_CODES:
        if code in name:
            return code
    return "UNKNOWN"


# ═══════════════════════════════════════════════════════════════════════════════
# ── UNIT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════
def extract_unit_file(file_bytes: bytes, filename: str):
    entity = detect_unit_entity(filename)
    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
    rows = df.values.tolist()
    results = []
    for i, row in enumerate(rows):
        if cv(row[1]) != "CERTIFICATE HOLDER":
            continue
        balance = 0.0
        for col in [23, 18, 16]:
            raw = row[col] if col < len(row) else None
            if raw is not None and str(raw).strip() not in ("", "nan"):
                try:
                    balance = float(raw)
                    break
                except Exception:
                    pass
        name_row = rows[i + 2] if i + 2 < len(rows) else []
        suffix_row = rows[i + 3] if i + 3 < len(rows) else []
        name = cv(name_row[1]) if len(name_row) > 1 else ""
        if not name:
            continue
        suffix = cv(suffix_row[1]) if len(suffix_row) > 1 else ""
        if suffix in UNIT_SUFFIXES:
            name = name + " " + suffix
        name = name.strip()
        investor = UNIT_MASTER.get(name, name)
        results.append({"entity": entity, "investor": investor, "balance": balance})
    return entity, results


def build_unit_excel(all_results) -> bytes:
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = wb.add_worksheet("Client Statement")
    hdr = wb.add_format({"bold": True, "font_name": "Arial", "font_size": 10, "bg_color": "#1F4E79", "font_color": "#FFFFFF", "align": "center", "valign": "vcenter"})
    body = wb.add_format({"font_name": "Arial", "font_size": 10})
    money = wb.add_format({"font_name": "Arial", "font_size": 10, "num_format": "#,##0.00;-#,##0.00;\"-\"", "align": "right"})
    for c, h in enumerate(["Entity", "Investor", "Entity | Investor", "Balance"]):
        ws.write(0, c, h, hdr)
    for r, rec in enumerate(all_results, 1):
        ws.write(r, 0, rec["entity"], body)
        ws.write(r, 1, rec["investor"], body)
        ws.write(r, 2, rec["entity"] + " | " + rec["investor"], body)
        ws.write(r, 3, rec["balance"], money)
    ws.set_column("A:A", 10)
    ws.set_column("B:B", 58)
    ws.set_column("C:C", 70)
    ws.set_column("D:D", 18)
    ws.set_row(0, 18)
    wb.close()
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# ── LOAN EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════
def extract_loan_file(file_bytes: bytes):
    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
    rows = df.values.tolist()
    bsa_rows = [i for i, row in enumerate(rows) if cv(row[0]) == "BORROWER STATEMENT OF ACCOUNT"]
    results = []
    detected_month = None

    for block_idx, start in enumerate(bsa_rows):
        end = bsa_rows[block_idx + 1] if block_idx + 1 < len(bsa_rows) else len(rows)
        name_row = rows[start + 12] if start + 12 < len(rows) else []
        raw_name = cv(name_row[1]) if len(name_row) > 1 else ""
        entity, borrower = LOAN_MASTER.get(raw_name, ("", raw_name))
        bal_row = rows[start + 7] if start + 7 < len(rows) else []
        balance = 0.0
        try:
            balance = float(bal_row[19]) if bal_row[19] is not None else 0.0
        except Exception:
            pass
        res_row = rows[start + 8] if start + 8 < len(rows) else []
        reserve = 0.0
        try:
            reserve = float(res_row[19]) if res_row[19] is not None else 0.0
        except Exception:
            pass

        latest_dt = None
        for i in range(start, end):
            r = rows[i]
            if isinstance(r[2], datetime.datetime):
                if latest_dt is None or r[2] > latest_dt:
                    latest_dt = r[2]

        if latest_dt and detected_month is None:
            detected_month = latest_dt

        interest = 0.0
        if latest_dt:
            last_pos = 0.0
            for i in range(start, end):
                r = rows[i]
                if isinstance(r[2], datetime.datetime):
                    if r[2].year == latest_dt.year and r[2].month == latest_dt.month:
                        try:
                            v = float(r[8])
                            if v > 0:
                                last_pos = v
                        except Exception:
                            pass
            interest = last_pos

        results.append({"entity": entity, "borrower": borrower, "balance": balance, "interest": interest, "reserve": reserve})

    return results, detected_month


def build_loan_excel(all_results, detected_month=None):
    if detected_month:
        month_str = detected_month.strftime("%B %Y")
        filename = f"Capspace Loans Reconciliation Automation v1.6 {month_str}.xlsx"
    else:
        filename = "Capspace Loans Reconciliation Automation v1.6.xlsx"

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    hdr = wb.add_format({"bold": True, "font_name": "Arial", "font_size": 10, "bg_color": "#1F4E79", "font_color": "#FFFFFF", "align": "center", "valign": "vcenter"})
    body = wb.add_format({"font_name": "Arial", "font_size": 10})
    money = wb.add_format({"font_name": "Arial", "font_size": 10, "num_format": "#,##0.00;-#,##0.00;\"-\"", "align": "right"})

    # ── Summary (extracted data) ──────────────────────────────────────────────
    ws = wb.add_worksheet("Summary")
    for c, h in enumerate(["Entity", "Borrower", "Statement Balance", "Interest for the month", "Reserve Balance"]):
        ws.write(0, c, h, hdr)
    for r, rec in enumerate(all_results, 1):
        ws.write(r, 0, rec["entity"], body)
        ws.write(r, 1, rec["borrower"], body)
        ws.write(r, 2, rec["balance"], money)
        ws.write(r, 3, rec["interest"], money)
        ws.write(r, 4, rec["reserve"], money)
    ws.set_column("A:A", 10)
    ws.set_column("B:B", 55)
    ws.set_column("C:E", 22)
    ws.set_row(0, 18)

    # ── Master ────────────────────────────────────────────────────────────────
    wm = wb.add_worksheet("Master")
    for r, row in enumerate(LOAN_MASTER_DATA):
        for c, val in enumerate(row):
            if val:
                wm.write(r, c, val, body)
    wm.set_column("A:A", 10)
    wm.set_column("B:B", 55)
    wm.set_column("C:C", 55)

    # ── BS sheets (placeholder headers) ──────────────────────────────────────
    for sname, stitle in [
        ("CPDF BS", "Capspace Private Debt Fund Balance Sheet (Please include account codes)"),
        ("CPL BS", "Capspace Pty Ltd Balance Sheet (Please include account codes)"),
        ("CDLOT BS", "Capspace Direct Loan Opportunity Trust Balance Sheet (Please include account codes)"),
        ("CDLOT2 BS", "Capspace Direct Loan Opportunity Trust Balance Sheet No 2 (Please include account codes)"),
    ]:
        wbs = wb.add_worksheet(sname)
        wbs.write(0, 0, stitle, body)

    wb.close()
    return output.getvalue(), filename


# ═══════════════════════════════════════════════════════════════════════════════
# ── INTEREST EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════
def detect_interest_entity(df) -> str:
    entity_name = str(df.iloc[1, 0]).strip()
    if 'No 2' in entity_name or 'No. 2' in entity_name:
        return 'CDLOT2'
    elif 'Direct Loan' in entity_name or 'DLOT' in entity_name:
        return 'CDLOT'
    else:
        return 'CPDF'


def is_interest_page_break(row) -> bool:
    v = str(row.iloc[0]).strip()
    return any(s in v for s in INTEREST_PAGE_BREAK_SIGNALS)


def is_interest_investor_header(row) -> bool:
    col0 = str(row.iloc[0]).strip()
    col2 = str(row.iloc[2]).strip()
    return (col0.isdigit() and col2 not in ('', 'nan', 'None')
            and col2 != 'Certificate Number')


def is_interest_summary_row(row) -> bool:
    col1 = str(row.iloc[1]).strip()
    col12 = row.iloc[12]
    col16 = row.iloc[16]
    return (col1 in ('', 'nan') and isinstance(col12, float)
            and isinstance(col16, float))


def detect_interest_month(df) -> str:
    try:
        parts = str(df.iloc[2, 0]).strip().split()
        if len(parts) >= 3:
            return f"{parts[1]} {parts[2]}"
    except Exception:
        pass
    return ""


def extract_interest_file(file_bytes: bytes):
    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
    entity = detect_interest_entity(df)
    month_label = detect_interest_month(df)
    results = []
    current_investor = None
    for _, row in df.iterrows():
        if is_interest_page_break(row):
            continue
        if is_interest_investor_header(row):
            investor_name = str(row.iloc[2]).strip()
            if investor_name != current_investor:
                current_investor = investor_name
        elif is_interest_summary_row(row) and current_investor:
            col12 = row.iloc[12]
            col16 = row.iloc[16]
            if isinstance(col12, float) and math.isnan(col12):
                continue
            try:
                pay_amt = float(col12)
            except Exception:
                pay_amt = 0.0
            try:
                interest = float(col16)
            except Exception:
                interest = 0.0
            try:
                principal = float(row.iloc[18])
            except Exception:
                principal = 0.0
            results.append({
                'investor': current_investor,
                'pay_amount': pay_amt,
                'interest_paid': interest,
                'principal_paid': principal,
                'in_payee': current_investor in INTEREST_PAYEE_LIST,
            })
            current_investor = None
    return entity, month_label, results


def build_interest_excel(results_by_entity, month_label: str = "") -> bytes:
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    hdr = wb.add_format({"bold": True, "font_name": "Arial", "font_size": 10,
                         "bg_color": "#1F4E79", "font_color": "#FFFFFF",
                         "align": "center", "valign": "vcenter"})
    body = wb.add_format({"font_name": "Arial", "font_size": 10})
    money = wb.add_format({"font_name": "Arial", "font_size": 10,
                           "num_format": "#,##0.00;-#,##0.00;\"-\"", "align": "right"})
    bool_fmt = wb.add_format({"font_name": "Arial", "font_size": 10})

    SHEET_LABELS = {
        'CPDF': 'From Mortgage Pool Distribution Audit Report CPDF',
        'CDLOT': 'From Mortgage Pool Distribution Audit Report DLOT',
        'CDLOT2': 'From Mortgage Pool Distribution Audit Report DLOT#2',
    }

    # ── Xero Contacts (placeholder header) ────────────────────────────────────
    ws_xero = wb.add_worksheet("Xero Contacts")
    for c, h in enumerate(["Investor", "Bank Account Number", "", "", "",
                            "Payee/Payor Name", "Transaction", "BSB",
                            "Bank Account", "Bank Account Number"]):
        ws_xero.write(0, c, h, hdr)
    ws_xero.set_column("A:A", 40)
    ws_xero.set_column("B:J", 18)

    # ── Payee sheet ────────────────────────────────────────────────────────────
    ws_payee = wb.add_worksheet("Payee")
    ws_payee.write(0, 0, "Xero Contacts", hdr)
    for i, name in enumerate(INTEREST_PAYEE_LIST, 1):
        ws_payee.write(i, 0, name, body)
    ws_payee.set_column("A:A", 55)

    # ── Entity sheets (CPDF, CDLOT, CDLOT2) ───────────────────────────────────
    for entity in ['CPDF', 'CDLOT', 'CDLOT2']:
        ws = wb.add_worksheet(entity)
        total_fmt = wb.add_format({"bold": True, "font_name": "Arial", "font_size": 10,
                                   "num_format": "#,##0.00;-#,##0.00;\"-\"", "align": "right"})
        ws.write(0, 0, "Investor", hdr)
        ws.write(0, 1, "Pay Amount", hdr)
        ws.write(0, 2, "Interest Paid", hdr)
        ws.write(0, 3, "Principal Paid", hdr)
        ws.write(0, 5, "With bank details in contacts?", hdr)
        ws.write(0, 7, SHEET_LABELS[entity], hdr)

        rows = results_by_entity.get(entity, [])
        for r, rec in enumerate(rows, 1):
            ws.write(r, 0, rec['investor'], body)
            ws.write_number(r, 1, float(rec['pay_amount'] or 0), money)
            ws.write_number(r, 2, float(rec['interest_paid'] or 0), money)
            ws.write_number(r, 3, float(rec['principal_paid'] or 0), money)
            ws.write_formula(r, 5, f'=IF(ISERROR(VLOOKUP(A{r+1},Payee!A:A,1,FALSE)),FALSE,TRUE)', bool_fmt)

        if rows:
            t = len(rows) + 1
            ws.write_number(t, 1, sum(float(rec['pay_amount'] or 0) for rec in rows), total_fmt)
            ws.write_number(t, 2, sum(float(rec['interest_paid'] or 0) for rec in rows), total_fmt)
            ws.write_number(t, 3, sum(float(rec['principal_paid'] or 0) for rec in rows), total_fmt)

        ws.set_column("A:A", 50)
        ws.set_column("B:D", 18)
        ws.set_column("F:F", 30)
        ws.set_column("H:H", 50)
        ws.set_row(0, 18)

    wb.add_worksheet("Temp")

    wb.close()
    return output.getvalue()
