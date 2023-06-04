# from flask_appbuilder import Model
# from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
# from sqlalchemy.orm import relationship

# class NilmModel(Model):
#     """
#     A class of the NILM models that have been pre-trained in the first part
#     """
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(50), unique=True, nullable=False)
#     description = Column(String(100), unique=True, nullable=True)

#     def __repr__(self) -> str:
#         return self.name


# class History(Model):
#     """
#     A class to save the hsitorical data of the users
#     """
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey('ab_user.id'), nullable = False)
#     timestamp = Column(DateTime,  nullable = False)    
#     power = Column(Float, nullable = False)




