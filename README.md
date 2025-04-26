gnucash-xml-split
=================

Split GnuCash XML files into files containing transaction in a certain period (e.g. a year).

This utility is used to split big GnuCash XML files into yearly basis. As I kept using GnuCash, the data file is getting larger and larger. However, GnuCash does not seem to willing to provide the functionality to split data files, only to add year end book-closing transactions. Hence the utility.

Usage
========
`gnucash-xml-split.py -i input.gnucash -o out.xml -y 2014`

`-i input.gnucash`
The input zipped GnuCash XML file. This file will stay not changed in the operation.
`-o out.xml`
The output GnuCash XML file. This file is a text XML file which not zipped. It would contain all transactions happen in the year specified by `-y`, all other transactions (either before or after the year) will be removed.
`-y 2014`
The year to extract transactions.

Other output files:
This utility will NOT add any transaction in the output file. Opening balancs are saved in QIF files. All transactions before the year will be used to calculate the opening balances, and all accounts except INCOME, EXPENSE, EQUITY accounts would included. As QIF format does not have currency information, accounts with different currencies will be save in different files. The generated file name would be `YearCurrency.qif`. In the above example, `2014USD.qif` would be generated for US dollars opening balance. You'll have to import the file in GnuCash manually. The opening balances comes from account: `Equity:Opening Balances:USD`. Different accounts will be used for different currencies.

Note
==========
It should be easy to modify the utility to extract transations in arbitrary period.

If you find any bug or inconvenience, feel free to open an issue. 
