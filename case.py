import os
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style='whitegrid', rc={'figure.figsize':(24,12)})

# Reads tsv files
# usecols were used to increase reading speed
companies = pd.read_csv('data/companies.tsv', sep='\t',
                        usecols=['companiesId', 'companiesName',
                                 'sectorKey', 'employeesName'])
deals = pd.read_csv('data/deals.tsv', sep='\t')
sectors = pd.read_csv('data/sectors.tsv', sep='\t')
contacts = pd.read_csv('data/contacts.tsv', sep='\t',
                       usecols=[' contactsId', 'contactsName'])

dfs = [companies, deals, sectors, contacts]
dfs_name = ['companies', 'deals', 'sectors', 'contacts']

for i in range(len(dfs)):
    removed_rows = 0
    for index, row in dfs[i].iterrows():
        try:
            # Encode row as latin
            row.str.encode('latin1')
        except UnicodeEncodeError:
            # Remove row that cannot be encoded as latin1
            dfs[i].drop(index, inplace=True)
            removed_rows += 1

    # Print number of removed rows
    print('Number of removed rows from {}: {}'.format(
        dfs_name[i],
        removed_rows,
        ))

# Removes spaces from column names
new_columns = dict(zip(contacts.columns, contacts.columns.str.strip()))
contacts.rename(new_columns, axis=1, inplace=True)

# Removes duplicated rows and counts them
init_rows = contacts.shape[0]
contacts.drop_duplicates(subset='contactsName', inplace=True)
final_rows = contacts.shape[0]
n_removed = init_rows - final_rows
print('Number of duplicate lines removed from contacts: {}'.format(n_removed))


def first_output() -> pd.DataFrame:
    """Generates a dataframe that enables the creation and analysis of
    the sold value by month and by contact. Also creates a csv file in
    output directory

    Returns:
        pd.DataFrame: Dataframe containing contact name, deal value and month
    """

    contacts_deals = deals.merge(contacts, on='contactsId', how='left')
    # Parse dealsDateCreated and set it as index
    contacts_deals['dealsDateCreated'] = contacts_deals['dealsDateCreated'].apply(
        lambda x: datetime.strptime(x, '%m/%d/%Y'))
    contacts_deals.set_index('dealsDateCreated', inplace=True)
    # Creates a date column containing 'mon'/YY
    contacts_deals['monthYear'] = contacts_deals.index.to_series().dt.strftime('%b/%y')
    # Filters columns needed to create the sold value by month and by contact
    needed_columns = ['contactsName', 'dealsPrice', 'monthYear']
    first_output = contacts_deals[needed_columns]

    first_output.to_csv('output/first_output.csv')

    return first_output

def second_output() -> pd.DataFrame:
    """Creates a dataframe containing information about the percentual sold 
    value for each sector of the industry. Also exports this csv file to
    output directory

    Returns:
        pd.DataFrame: Dataframe containing the percentage of value by sector
    """

    companies_deals = deals.merge(companies[['companiesId', 'sectorKey']],
                                             on='companiesId', how='left')
    sector_deals = companies_deals.merge(sectors, on='sectorKey', how='left')

    sector_value = sector_deals.groupby('sector').sum().reset_index()
    sector_percent = sector_value['dealsPrice'] / sector_value['dealsPrice'].sum()
    sector_value['dealsPercent'] = sector_percent.round(3)
    sector_value.sort_values('dealsPercent', ascending=False, inplace=True)

    sector_value[['sector', 'dealsPercent']].to_csv('output/second_output.csv',
                                                    index=False)
    
    return sector_value[['sector', 'dealsPercent']]

def get_plots():
    """Creates the example plots with the csv files of the first output"""

    grouped_by_month = f_out.resample('MS').sum()
    grouped_by_month['monthYear'] = grouped_by_month.index.to_series().dt.strftime('%b/%y')
    value_month = sns.barplot(x='monthYear', y='dealsPrice',
                              data=grouped_by_month,
                              color='dodgerblue')
    
    # Sets legend, title and x/y labels
    value_month.legend(['Sold Value'])
    value_month.set_title('Total Sold Value by Month', fontsize=20)
    value_month.set(xlabel='Month/Year', ylabel='Sold Value')

    # Adds label to each bar
    for i, bar in enumerate(value_month.patches):
        h = bar.get_height()
        value_month.text(
            i, # bar index
            h+1000, # y coordinate of text
            '{}'.format(int(h)), # y label
            ha='center',
            va='center',
            size=12,
        )
    
    # Saves plot
    value_month.get_figure().savefig('output/value_by_month.png')

    # Clear figure
    plt.clf()

    # Second
    grouped_by_contact = f_out.groupby('contactsName').sum().reset_index()
    grouped_by_contact.sort_values('dealsPrice', ascending=False, inplace=True)
    value_contacts = sns.barplot(x='contactsName', y='dealsPrice',
                                 data=grouped_by_contact, color='dodgerblue')
    
    # Sets legend, title and x/y labels
    value_contacts.legend(['Sold Value'])
    value_contacts.set_title('Total Sold Value by Contact', fontsize=20)
    value_contacts.set(xlabel='Month/Year', ylabel='Sold Value')
    value_contacts.set_xticklabels(value_contacts.get_xticklabels(),
                                   rotation=45)

    # Adds label to each bar
    for i, bar in enumerate(value_contacts.patches):
        h = bar.get_height()
        value_contacts.text(
            i, # bar index
            h+1000, # y coordinate of text
            '{}'.format(int(h)), # y label
            ha='center',
            va='center',
            size=10,
        )

    # Saves plot
    value_contacts.get_figure().savefig('output/value_by_contact.png')

    pass

if __name__ == '__main__':
    try:
        os.mkdir('output')
    except FileExistsError:
        pass
    f_out = first_output()
    s_out = second_output()
    get_plots()
