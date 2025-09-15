from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser):
    # 手机号
    mobile = models.CharField(max_length=11, unique=True, blank=False)
    # 头像信息 以年月日作为文件名
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/',default='default_avatar.png', blank=True)
    # 简介信息
    user_desc = models.CharField(max_length=500, blank=True)
    # 修改认证字段为手机号
    USERNAME_FIELD = 'mobile'

    # 创建超级用户需要输入的字段
    REQUIRED_FIELDS = ['username', 'email']


    class Meta:
        db_table = 'tb_users'  # 修改表名
        verbose_name = '用户管理'  # admin后台显示
        verbose_name_plural = verbose_name  # admin后台显示

    def __str__(self):
        return self.mobile


