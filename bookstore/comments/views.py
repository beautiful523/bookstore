from django.http import JsonResponse
from comments.models import Comments
from books.models import Books
from users.models import Passport
import json
import redis
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def comment(request, books_id):
	if request.method == "GET":
		comments = Comments.objects.filter(book_id=books_id)
		data = []
		for c in comments:
			data.append({
				'user_id': c.user_id,
				'content': c.content,
			})
		res = {
			'code': 200,
			'data': data,
		}
		return JsonResponse(res)
	
	else:
		params = json.loads(request.body.decode('utf-8'))
		books_id = params.get('book_id')
		user_id = params.get('user_id')
		content = params.get('content')
		print(content)
		book = Books.objects.get(id=books_id)
		user = Passport.object.get(id=user_id)
		
		new_comment = Comments(book=book, user=user, content=content)
		new_comment.save()
		
		return JsonResponse({
			'code': 200,
			'msg': '评论成功',
		})
