from django.db import models


# 所有模型的基类
class BaseModel(models.Model):
	# verbose_name就是别名
	is_delete = models.BooleanField(default=False, verbose_name="删除")
	# auto_now_add与auto_now不能手动修改的意思
	# add是在创建的时候
	create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
	update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
	
	class Meta:
		# 设置 abstract=True 该类就不能创建任何数据表。
		# 然而如果将它做为其他 model 的基类，那么该类的字段就会被添加到子类中。
		# 抽象基类和子类如果含有同名字段，就会导致错误(Django 将抛出异常)。
		abstract = True
