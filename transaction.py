from google.appengine.ext import db

from datetime import date


class Transaction(db.Model):
    userid = db.StringProperty()
    
    origDate = db.DateProperty()
    origDescription = db.StringProperty()
    origOriginalDescription = db.StringProperty()
    origAmount = db.FloatProperty()
    origTransactionType = db.StringProperty()
    origTransactionCategory = db.StringProperty()
    origAccountName = db.StringProperty()
    origLabels = db.StringProperty()
    origNotes = db.StringProperty(multiline=True)
    
    date = db.DateProperty()
    transactionCategory = db.StringProperty()
    
    budgetCategory = db.StringProperty()
    
    @staticmethod
    def from_mint_transaction(transactionDate, description, originalDescription, 
                              amount, transactionType, transactionCategory, accountName, 
                              labels, notes):
        obj = Transaction()
        
        mdy = transactionDate.split("/")
        mdy = [int(s) for s in mdy]
        obj.origDate = date(year=mdy[2], month=mdy[0], day=mdy[1])
        
        obj.origDescription = description
        obj.origOriginalDescription = originalDescription
        obj.origAmount = float(amount)
        obj.origTransactionType = transactionType
        obj.origTransactionCategory = transactionCategory
        obj.origAccountName = accountName
        obj.origLabels = labels
        obj.origNotes = notes
        
        return obj