from django.db import models
from db import BaseModels
from hashlib import sha1


# 用户表的管理器类(自定义的管理器)
class PassportManager(models.Manager):
	# 添加一个用户信息的方法
	def add_one_passport(self, user_name, password, email):
		passport = self.create(user_name=user_name, password=self.get_hash(password), email = email)
		return passport
	
	# 根据用户名密码查找账户信息的方法
	def get_one_passport(self, user_name, password):
		passport = self.get(user_name=user_name, password = self.get_hash(password))
		return passport
	
	# 得到哈希字符串的方法(给密码加密)
	def get_hash(self, password):
		sh = sha1()
		sh.update(password.encode("utf-8"))
		return sh.hexdigest()
	
	
		
# 用户类
class Passport(BaseModels.BaseModel):
	user_name = models.CharField(max_length=20, verbose_name="用户名")
	password = models.CharField(max_length=40, verbose_name="密码")
	email = models.EmailField(verbose_name="邮箱")
	is_active = models.BooleanField(default=False, verbose_name="激活")
	user_phone = models.CharField(max_length=11, default='未填写', verbose_name='联系电话')
	user_address = models.CharField(max_length=256, default='未填写', verbose_name='收件地址')


	# 用户表的管理器实例
	object = PassportManager()
	class Meta:
		# 定义用户表在数据库中的名字
		db_table = "s_user_account"


# 收货地址表的管理器
class RecipientManager(models.Manager):
	# 查询指定用户的默认收货地址
	def get_default_recipient(self, passport_id):
		try:
			recipient = self.get(passport_id=passport_id, is_default=True)
		except self.model.DoesNotExist:
			recipient = None
		return recipient
	
	# 增加一条收货地址
	def add_one_recipient(self, passport_id, recipient_name, recipient_address, postal_code, recipient_phone):
		exist_default_recipient = self.get_default_recipient(passport_id=passport_id)
		if exist_default_recipient:
			is_default = False
		else:
			is_default = True
		recipient = self.create(
			passport_id=passport_id,
			recipient_name=recipient_name,
			recipient_address=recipient_address,
			postal_code=postal_code,
			recipient_phone=recipient_phone,
			is_default=is_default
		)
		return recipient


class Recipient(BaseModels.BaseModel):
	recipient_name = models.CharField(max_length=20, verbose_name='收件人')
	recipient_address = models.CharField(max_length=256, verbose_name='收件地址')
	postal_code = models.CharField(max_length=6, verbose_name='邮政编码')
	recipient_phone = models.CharField(max_length=11, verbose_name='联系电话')
	is_default = models.BooleanField(default=False, verbose_name='是否默认')
	# ForeignKey一对多，字段定义在多端，一个账户可以有多条收货信息
	passport = models.ForeignKey('Passport', verbose_name='所属账户')
	
	objects = RecipientManager()
	
	class Meta:
		db_table = 's_user_recipient'
