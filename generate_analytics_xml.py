import random
import os
import shutil

output_path = r"c:\Databricks_project\xml_to_snowflake\datasets\analytics\samples\analytics.xml"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
samples_path = r"c:\Databricks_project\xml_to_snowflake\samples\analytics\analytics.xml"
os.makedirs(os.path.dirname(samples_path), exist_ok=True)

countries = ['GB', 'US', 'DE', 'FR', 'JP', 'CA', 'AU', 'CH', 'NL', 'SG', 'IT', 'ES', 'BR', 'IN']
cntry_srcs = ['L', 'NL', 'B', 'M', 'R', 'IDX', 'ISO']
cntry_types = ['IDX', 'DOM', 'RISK', 'INCORP', 'LEGAL']
currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
cusip_types = ['CUSIP', 'ISIN', 'SEDOL', 'VALOREN']
date_convs = ['30E360', 'ACT360', 'ACTACT', '30360']
call_types = ['A', 'E', 'B', 'N', 'X']
cpn_types = ['F', 'V', 'Z', 'S']
coup_freqs = ['S', 'A', 'Q', 'M']

companies = [
    'GLOBAL AUTO HOLDINGS PLC',
    'APEX FINANCIAL CORP',
    'TITAN ENERGY LOGISTICS LLC',
    'VORTEX PHARMACEUTICALS INC',
    'QUANTUM SEMICONDUCTOR NV',
    'BEACON REAL ESTATE TRUST',
    'SOLARIS INFRASTRUCTURE LTD',
    'NEXUS TELECOM GROUP SA',
    'ORION DEFENSE AEROSPACE PLC',
    'ZENITH MARITIME CARRIERS'
]

def generate_record(idx):
    accrual_dt = f"{random.randint(1,12)}/{random.randint(1,28)}/202{random.randint(2,5)}"
    announce_dt = f"{random.randint(1,12)}/{random.randint(1,28)}/202{random.randint(2,5)}"
    change_dt = f"{random.randint(1,12)}/{random.randint(1,28)}/2026 {random.randint(10,23)}:{random.randint(10,59)}:{random.randint(10,59)}.{random.randint(100,999)}"
    first_pay_dt = f"{random.randint(1,12)}/{random.randint(1,28)}/202{random.randint(4,6)}"
    first_settle_dt = f"{random.randint(1,12)}/{random.randint(1,28)}/202{random.randint(2,4)}"
    amt_isu = random.choice([50000000, 100000000, 250000000, 525000000, 750000000, 1000000000, 1500000000])
    calc_type = random.randint(1, 5)
    call_mand = random.choice(['Y', 'N'])
    call_type = random.choice(call_types)
    instmt_type = random.choice(['UNKNOWN', 'CORP_BOND', 'SECURED_NOTE', 'MTN', 'SUB_DEBT'])
    compound_flag = random.randint(0, 1)
    country = random.choice(countries)
    coupon_fix = f"{random.uniform(2.5, 12.5):.3f}"
    coup_freq = random.choice(coup_freqs)
    cpn_type = random.choice(cpn_types)
    currency = random.choice(currencies)
    cusip = f"{random.randint(1000,9999):04d}{random.choice(['AA','AB','AC','BA','BB','GA','GAA'])}{random.randint(1,9)}"
    company = random.choice(companies)
    date_conv = random.choice(date_convs)
    flag_144a = random.choice(['Y', 'N'])
    flag_reg_s = random.choice(['Y', 'N'])
    maturity_dt = f"{random.randint(1,12)}/{random.randint(1,28)}/20{random.randint(28,45)}"
    issue_price = f"{random.uniform(97.5, 102.5):.3f}"

    cc_records = []
    for _ in range(2):
        c_src = random.choice(cntry_srcs)
        c_type = random.choice(cntry_types)
        cc_records.append(f"""        <COUNTRY_CLASSIFICATION_record>
            <CNTRY>{country}</CNTRY>
            <CNTRY_SRC>{c_src}</CNTRY_SRC>
            <CNTRY_TYPE>{c_type}</CNTRY_TYPE>
        </COUNTRY_CLASSIFICATION_record>""")
    cc_block = '\n'.join(cc_records)

    isin = f"{country}{random.randint(100000000, 999999999)}{random.randint(0,9)}"
    ric = f"0x{random.randint(10000000, 99999999):08x}cfc00ac{random.randint(1,9)}"
    sedol = f"{random.choice(['B','C','D','E'])}{random.randint(10000,99999)}{random.randint(0,9)}"
    wkn = f"A{random.randint(100,999)}T{random.randint(10,99)}"

    c2_records = [
        f"""        <CUSIP2_record>
            <CODE>A</CODE>
            <IDENTIFIER>{cusip}</IDENTIFIER>
        </CUSIP2_record>""",
        f"""        <CUSIP2_record>
            <CODE>C</CODE>
            <IDENTIFIER>{sedol}</IDENTIFIER>
        </CUSIP2_record>""",
        f"""        <CUSIP2_record>
            <CODE>I</CODE>
            <IDENTIFIER>{isin}</IDENTIFIER>
        </CUSIP2_record>""",
        f"""        <CUSIP2_record>
            <CODE>R</CODE>
            <IDENTIFIER>{ric}</IDENTIFIER>
        </CUSIP2_record>""",
        f"""        <CUSIP2_record>
            <CODE>W</CODE>
            <IDENTIFIER>{wkn}</IDENTIFIER>
        </CUSIP2_record>"""
    ]
    c2_block = '\n'.join(c2_records)

    alias_code = random.randint(8000, 8999)
    alias_id = random.randint(100000000, 999999999)
    alias_purpose = random.choice(['DEBTID', 'LOANID', 'SECURITYID', 'INTERNALREF'])
    alias_block = f"""        <CUSIP_ALIAS_record>
            <CODE>{alias_code}</CODE>
            <IDENTIFIER>{alias_id}</IDENTIFIER>
            <PURPOSE>{alias_purpose}</PURPOSE>
        </CUSIP_ALIAS_record>"""

    return f"""    <ASSET>
        <CLASS>BND_CORP</CLASS>
        <ACCRUAL_DT>{accrual_dt}</ACCRUAL_DT>
        <AMT_ISU>{amt_isu}</AMT_ISU>
        <ANNOUNCE_DT>{announce_dt}</ANNOUNCE_DT>
        <CALC_TYPE>{calc_type}</CALC_TYPE>
        <CALL_MANDATORY>{call_mand}</CALL_MANDATORY>
        <CALL_TYPE>{call_type}</CALL_TYPE>
        <CD_INSTMT_TYPE>{instmt_type}</CD_INSTMT_TYPE>
        <CHANGE_DT>{change_dt}</CHANGE_DT>
        <COMPOUND_FLAG>{compound_flag}</COMPOUND_FLAG>
        <COUNTRY>{country}</COUNTRY>
        <COUNTRY_CLASSIFICATION_set SIZE="2">
{cc_block}
        </COUNTRY_CLASSIFICATION_set>
        <COUPON_FIX>{coupon_fix}</COUPON_FIX>
        <COUP_FREQ>{coup_freq}</COUP_FREQ>
        <CPN_TYPE>{cpn_type}</CPN_TYPE>
        <CURRENCY>{currency}</CURRENCY>
        <CUSIP>{cusip}</CUSIP>
        <CUSIP2_set SIZE="5">
{c2_block}
        </CUSIP2_set>
        <CUSIP_ALIAS_set SIZE="1">
{alias_block}
        </CUSIP_ALIAS_set>
        <CUSIP_TYPE>{random.choice(cusip_types)}</CUSIP_TYPE>
        <DATE_CONV>{date_conv}</DATE_CONV>
        <DESC_INSTMT>{company}</DESC_INSTMT>
        <END_ADJ_FLAG>{random.choice(['Y', 'N'])}</END_ADJ_FLAG>
        <FIRST_PAY_DT>{first_pay_dt}</FIRST_PAY_DT>
        <FIRST_SETTLE_DT>{first_settle_dt}</FIRST_SETTLE_DT>
        <FLAG_144A>{flag_144a}</FLAG_144A>
        <FLAG_REG_S>{flag_reg_s}</FLAG_REG_S>
        <ISSUE_PRICE>{issue_price}</ISSUE_PRICE>
        <MATURITY_DT>{maturity_dt}</MATURITY_DT>
    </ASSET>"""

target_bytes = int(5.1 * 1024 * 1024)  # ~5.1 MB
header_prefix = '<?xml version="1.0" encoding="UTF-8"?>\n<ASSETS ASOF_DATE="5/11/2026" CREATE_DATE="5/11/2026" RECORDS="'
header_suffix = '">\n'

print("Writing records...")
records = []
total_size = 0
idx = 0
while total_size < target_bytes:
    idx += 1
    rec = generate_record(idx)
    records.append(rec)
    total_size += len(rec.encode('utf-8')) + 1

header = f'{header_prefix}{idx:06d}{header_suffix}'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(header)
    for rec in records:
        f.write(rec)
        f.write('\n')
    f.write('</ASSETS>\n')

final_size = os.path.getsize(output_path)
print(f"Generated {output_path}")
print(f"Records: {idx}, File size: {final_size / (1024 * 1024):.2f} MB ({final_size:,} bytes)")

shutil.copy2(output_path, samples_path)
print(f"Copied to {samples_path}")

