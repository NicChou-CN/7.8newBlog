from django.shortcuts import render
from django.http import HttpResponseBadRequest, HttpResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http.response import JsonResponse
from utils.response_code import RETCODE
from django.shortcuts import redirect
from django.urls import reverse
import logging
logger = logging.getLogger('django')
from random import randint
from libs.yuntongxun.sms import CCP
from django.db import DatabaseError
import re
from users.models import User
# Create your views here.

from django.views import View


# 注册视图
class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')
    # 注册思路
    def post(self, request):
        # 接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        # 确认密码
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')
        # 验证数据
            # 参数是否齐全
            # 手机号格式是否正确
            # 密码是否符合格式
            # 密码是否一直
            # 短信验证码是否跟redis中的一致
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('缺少必要参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式错误')
        # 密码格式 8-20个字母或数字下划线
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位的字母或数字下划线密码')
        if password != password2:
            return HttpResponseBadRequest('两次密码输入不一致')
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if redis_sms_code.decode() != sms_code:
            return HttpResponseBadRequest('短信验证码错误')
        # 将用户信息保存数据库中
        try:
            #create_user可使用系统的方法对密码进行加密
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')
        from django.contrib.auth import login
        login(request, user)
        # 返回相应数据到指定页面中
        # 目前为暂时的注册成功 后续会进行添加
        # redirect 进行重定向
        # reverse 是可以通过namespace:name 来获取到对应的路由
        response =  redirect(reverse('home:index'))
        # 设置cookie信息 用于方便首页中用户信息展示的判断和用户信息的展示
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username,max_age=7*24*3600)
        return response
class ImageCodeView(View):
    def get(self, request):
        # 接收前端传递的uuid
        uuid = request.GET.get('uuid')
        # 判断uuid是否获取到
        if uuid is None:
            return HttpResponseBadRequest('没有传递uuid')
        # 调用Captcha生成图片验证码（图片二进制，图片内容）
        text, image = captcha.generate_captcha()
        # 将图片内容保存到redis中
        # uuid作为key 图片内容作为value
        redis_conn = get_redis_connection('default')
        # key设置为uuid
        # seconds  设置为秒数 过期时间
        # values 为图片二进制内容
        redis_conn.setex('img:%s' % uuid, 300, text)
        # 图片内容返回给前端
        # 保存图片验证码文本
        return HttpResponse(image, content_type='image/jpeg')


class SmsCodeView(View):
    def get(self, request):
        # 接收参数(查询字符串形式传递过来)
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 参数验证
        #   参数是否齐全
        if not all([mobile, image_code, uuid]):
            return JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errmsg':'缺少必要参数'})
        #   图片验证码的验证
        #      链接redis  获取redis中的图片验证码
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)
        #      判断图片验证码是否存在
        if redis_image_code is None:
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片验证码已过期'})
        #      如果图片验证码未过期 删除图片验证码
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        #      比对图片验证码 (大小写不敏感)
        #      redis的数据是Bytes类型
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片验证码错误'})
        # 生成短信验证码
        sms_code = '%04d' % randint(0, 9999)
        # 为了后期比对方便 将短信验证码记录到日志中
        logger.info(sms_code)
        # 保存短信验证码到redis中 过期时间设置为300s 5分钟
        redis_conn.setex('sms:%s' %mobile, 300, sms_code)
        # 发送短信
        CCP().send_template_sms(mobile, [sms_code,5], 1)
        # 返回响应 前端60秒倒计时处理
        return JsonResponse({'code':RETCODE.OK,'errmsg':'短信发送成功'})


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')
    def post(self, request):
        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 参数验证
        #   验证手机号
        #   验证密码
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式错误')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位的字母或数字下划线密码')
        # 用户认证登录
        # 采用系统自带的认证方法进行认证
        # 如果认证成功 返回user对象
        # 如果我们的用户名和密码不正确 返回none
        from django.contrib.auth import authenticate
        # 默认的认证方法是针对username字段进行用户名的判断
        # 当前的判断信息是手机号，需更改认证字段
        # 我们需要到user模型中进行修改 等测试出现问题再修改
        user = authenticate(mobile=mobile, password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')
        # 状态保持
        from django.contrib.auth import login
        login(request, user)
        # 根据用户选择的是否记住登录状态进行判断
        # 为了首页显示 我们需要设置的cookie信息


        # 如果查询字段有next要跳转到个人信息页面

        next_page = request.GET.get('next')
        if next_page:
            response = redirect(next_page)
        else:
            response = redirect(reverse('home:index'))
        if remember != 'on': # 没有记住用户信息
            request.session.set_expiry(0) # 浏览器关闭之后即忘记
            response.set_cookie('is_login', True) # 设置cookie状态
            response.set_cookie('username', user.username, max_age=14*24*3600)
        else: # 记住用户信息
            request.session.set_expiry(None) # 默认为记住两周
            response.set_cookie('is_login', True, max_age=14*24*3600)
            response.set_cookie('username', user.username,max_age=14*24*3600)
        # 返回相应
        return response
from django.contrib.auth import logout
class LogoutView(View):
    def get(self, request):
        # 清理session
        logout(request)
        # 重定向到首页
        response = redirect(reverse('home:index'))
        # 删除cookie中is_log信息
        response.delete_cookie('is_login')
        # 返回响应
        return response

class ForgetPasswordView(View):
    def get(self, request):
        return render(request, 'forget_password.html')
    def post(self, request):
        # 接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')
        # 数据验证
          # 参数是否齐全
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('缺少必要参数')
          # 手机号是否符合规则
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式错误')
          # 密码是否符合规则
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位的字母或数字下划线密码')
          # 判断两次密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')
          # 手机验证码的比对分析
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if redis_sms_code.decode() != sms_code:
            return HttpResponseBadRequest('短信验证码错误')
        # 根据手机号进行用户信息的查询
        try:
            user = User.objects.get(mobile=mobile)
        # 如若不存在 即可进行创建
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
            except:
                return HttpResponseBadRequest('修改失败m,请稍后再试')
        else:
            # 如果用户信息存在 即可进行修改
            user.set_password(password)
            user.save()
        # 以上都满足时 进行跳转登陆界面
        response = redirect(reverse('users:login'))
        # 返回相应
        return  response
from django.contrib.auth.mixins import LoginRequiredMixin
# LoginRequiredMixin
# 如果用户未登录的话就会进行跳转
# 默认跳转链接为 accounts/login/?next=XXX
class UserCenterView(LoginRequiredMixin,View):
    def get(self, request):
        # 获取登录用户的信息
        user = request.user
        # 组织用户的信息
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'avatar': user.avatar.url if user.avatar else None,
            'user_desc': user.user_desc
        }
        return render(request,'center.html',context=context)
    def post(self, request):
        # 接收参数
        user = request.user
        username = request.POST.get('username',user.username)
        user_desc = request.POST.get('desc',user.user_desc)
        avatar = request.FILES.get('avatar')
        # 接收参数后将参数保存起来
        try:
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败,请稍后再试')
        # 刷新当前页面（进行重定向操作）
        response = redirect(reverse('users:center'))
        # 更新cookie信息（用户名）
        response.set_cookie('username',
                            user.username,
                            max_age=14*24*3600
                            )
        # 返回相应
        return response
from home.models import ArticleCategory,Article
class WriteBlogView(LoginRequiredMixin,View):
    def get(self, request):
        # 获取分类信息
        categories = ArticleCategory.objects.all()
        context = {
            'categories': categories,
        }
        return render(request, 'write_blog.html',context=context)
    def post(self, request):
        # 接收数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        title = request.POST.get('title')
        summary = request.POST.get('sumary')
        content = request.POST.get('content')
        tags = request.POST.get('tags')
        user = request.user
        # 验证数据
        #     验证参数是否齐全
        if not all([title, category_id, summary, content,title]):
            return HttpResponseBadRequest('参数不齐全')
        #      验证分类ID
        try:
            category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类信息')
        # 数据入库
        try:
            article = Article.objects.create(
                author=user,
                # 接收封面信息
                avatar=avatar,
                title=title,
                category=category,
                tags = tags,
                summary=summary,
                content=content
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败,请稍后再试')
        # 跳转到指定页面
        response = redirect(reverse('home:index'))
        return response
