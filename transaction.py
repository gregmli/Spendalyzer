from google.appengine.ext import db

from datetime import date, datetime


class Transaction(db.Model):
    TYPE_DEBIT = "debit"
    TYPE_CREDIT = "credit"
    
    userid = db.StringProperty()
    
    #origDate = db.DateProperty()
    origDescription = db.StringProperty(indexed=False)
    origOriginalDescription = db.StringProperty(indexed=False)
    origAmount = db.FloatProperty(indexed=False)
    origTransactionType = db.StringProperty()
    #origCategory = db.StringProperty()
    origAccountName = db.StringProperty(indexed=False)
    origLabels = db.StringProperty(indexed=False)
    origNotes = db.StringProperty(multiline=True, indexed=False)
    
    transactionDate = db.DateProperty()
    overriddenDate = db.BooleanProperty(default=False, indexed=False)
    transactionCategory = db.StringProperty()
    overriddenCategory = db.BooleanProperty(default=False, indexed=False)
    
    created = db.DateTimeProperty(auto_now_add=True, indexed=False)
    modified = db.DateTimeProperty(auto_now_add=True, indexed=False)
    
    def getAmount(self):
        if (self.origTransactionType == Transaction.TYPE_DEBIT):
            return -self.origAmount
        
        return self.origAmount
    
        
    def getTransactionDate(self):
        if (self.transactionDate):
            return self.transactionDate
        
        return self.origDate
    
    def getTransactionCategory(self):
        if (self.transactionCategory):
            return self.transactionCategory
        
        return self.origCategory
    
    
    @staticmethod
    def importMintTransaction(userid, transactionDate, description, originalDescription, 
                              amount, transactionType, category, accountName, 
                              labels, notes):
        
        # this should be enough information to uniquely identify a transaction
        # if I one day implement updating of existing transactions. Note that category,
        # description, and other user-modifiable fields are not part of the key
        
        key = userid + transactionDate + amount + transactionType + accountName + originalDescription
        
        obj = Transaction.get_or_insert(key)
        
        obj.userid = userid
        
        obj.origDescription = description
        obj.origOriginalDescription = originalDescription
        obj.origAmount = float(amount)
        obj.origTransactionType = transactionType
        obj.origAccountName = accountName
        obj.origLabels = labels
        obj.origNotes = notes
        
        if (not obj.overriddenDate):
            mdy = transactionDate.split("/")
            mdy = [int(s) for s in mdy]       
            obj.transactionDate = date(year=mdy[2], month=mdy[0], day=mdy[1])
            
        if (not obj.overriddenCategory):
            obj.transactionCategory = category
            
        obj.modified = datetime.now()
        
        return obj