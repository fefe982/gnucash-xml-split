import argparse
import csv
import decimal

import gnucash_base as gb

parser = argparse.ArgumentParser(
    description="Generate GnuCash transaction (in csv) to meet the final balance requirement"
)
parser.add_argument("-i", "--input", help="input file name", required=True)
parser.add_argument("-o", "--output", help="csv output file name", required=True)
parser.add_argument("-b", "--balance", help="csv file contains the final balance", required=True)
args = parser.parse_args()


xmltree = gb.getElementTreeFromFile(args.input)
root = xmltree.getroot()


for book in root.findall("./{http://www.gnucash.org/XML/gnc}book"):
    accountdict = {}
    for account in book.findall("{http://www.gnucash.org/XML/gnc}account"):
        name = gb.getElementText(account, "{http://www.gnucash.org/XML/act}name")
        guid = gb.getElementText(account, "{http://www.gnucash.org/XML/act}id")
        actype = gb.getElementText(account, "{http://www.gnucash.org/XML/act}type")
        description = account.find("{http://www.gnucash.org/XML/act}description")
        if description is not None:
            description = description.text
        if actype == "ROOT":
            parent = None
            commodity = None
        else:
            parent = gb.getElementText(account, "{http://www.gnucash.org/XML/act}parent")
            commodity = gb.getElementText(
                account, "{http://www.gnucash.org/XML/act}commodity/{http://www.gnucash.org/XML/cmdty}id"
            )
        accountdict[guid] = gb.Account(
            name=name, description=description, guid=guid, parent=parent, actype=actype, commodity=commodity
        )
    for acc_key, account in accountdict.items():
        if account.actype == "ROOT":
            account.name_full = ""
        else:
            ancestor = [account, accountdict[account.parent]]
            while len(ancestor) > 1:
                ances = ancestor[-1]
                curr = ancestor[-2]
                if ances.actype == "ROOT":
                    curr.name_full = curr.name
                    ancestor.pop()
                elif ances.name_full is not None:
                    curr.name_full = ances.name_full + ":" + curr.name
                    ancestor.pop()
                else:
                    ancestor.append(accountdict[ances.parent])
    for transaction in book.findall("./{http://www.gnucash.org/XML/gnc}transaction"):
        datestr = gb.getElementText(
            transaction, "./{http://www.gnucash.org/XML/trn}date-posted/{http://www.gnucash.org/XML/ts}date"
        )
        for split in transaction.findall(
            "{http://www.gnucash.org/XML/trn}splits/{http://www.gnucash.org/XML/trn}split"
        ):
            quantity = gb.getElementText(split, "{http://www.gnucash.org/XML/split}quantity")
            account = accountdict[gb.getElementText(split, "{http://www.gnucash.org/XML/split}account")]
            num, denom = quantity.split("/")
            account.balance = account.balance + decimal.Decimal(num) / decimal.Decimal(denom)
    balancedict = {}
    for acc_key, account in accountdict.items():
        if (
            account.actype != "ROOT"
            and account.actype != "INCOME"
            and account.actype != "EXPENSE"
            and account.actype != "EQUITY"
            and account.balance != 0
        ):
            balancedict[account.name_full] = account.balance
    total = decimal.Decimal(0)
    with (
        open(args.balance, "r", encoding="utf-8", newline="") as inf,
        open(args.output, "w", encoding="utf-8", newline="") as outf,
    ):
        reader = csv.reader(inf)
        writer = csv.writer(outf)
        for row in reader:
            if row[0] not in balancedict:
                print(f"Account {row[0]} not found in the balance file")
                continue
            diff = decimal.Decimal(row[1]) - balancedict[row[0]]
            writer.writerow([row[0], -diff])
            total += diff
    print(f"Total: {total}")
