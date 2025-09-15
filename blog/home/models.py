from django.db import models
from django.utils import timezone
from users.models import User
# Create your models here.

class ArticleCategory(models.Model):
    # 文章分类

    # 文章标题
    title = models.CharField(max_length=100, blank=True)
    #分类的创建时间
    created = models.DateTimeField(default=timezone.now)
    #admin站点显示----调试查看方便
    def __str__(self):
        return self.title
    # 修改表名
    class Meta:
        verbose_name = 'tb_category' # 修改表名
        verbose_name = '类别管理' #admin站点显示
        verbose_name_plural = verbose_name
class Article(models.Model):
    # 作者
    # 参数ondelete表示关联外键的数据被删除时，本表中的数据应该如何处理 保证了数据一致性
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # 标题图
    avatar = models.ImageField(upload_to='article/%Y%m%d/', blank=True)
    # 标题
    title = models.CharField(max_length=20, blank=True)
    # 分类
    category = models.ForeignKey(ArticleCategory,null=True,blank=True, on_delete=models.CASCADE,related_name='article')
    # 标签
    tags = models.CharField(max_length=20, blank=True)
    # 摘要信息
    summary = models.CharField(max_length=200, blank=True)
    # 文章正文
    content = models.TextField(max_length=20000, blank=True)
    # 浏览量
    total_views = models.PositiveIntegerField(default=0)
    # 评论量
    comment_count = models.PositiveIntegerField(default=0)
    # 文章的创建时间
    created = models.DateTimeField(default=timezone.now)
    # 文章的修改时间
    updated = models.DateTimeField(auto_now=True)

    # 修改表名以及admin展示的配置信息
    class Meta:
        db_table = 'tb_article'
        ordering = ['-created']
        verbose_name = '文章管理'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.title


class Comment(models.Model):
    # 评论内容
    content = models.TextField(max_length=20000, blank=True)
    # 评论文章
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True)
    # 评论用户
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    # 评论时间
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.article.title
    class Meta:
        db_table = 'tb_comment'
        verbose_name = '评论管理'
        verbose_name_plural = verbose_name