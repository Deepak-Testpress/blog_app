from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Post
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from taggit.models import Tag


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = "posts"
    paginate_by = 3
    template_name = "blog/post/list.html"


class PostListByTagview(ListView):
    context_object_name = "posts"
    paginate_by = 3
    template_name = "blog/post/list.html"

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(Tag, slug=self.kwargs.get("tag_slug"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Post.published.filter(tags__in=[self.tag])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["tag"] = self.tag
        return data


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        slug=post,
        status="published",
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )
    comments = post.comments.filter(active=True)
    new_comment = None

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "comments": comments,
            "new_comment": new_comment,
            "comment_form": comment_form,
        },
    )


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status="published")
    sent = False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = (
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}'s comments: {cd['comments']}"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email="deepak@testpress.in",
                recipient_list=[cd["to"]],
            )
            sent = True

    else:
        form = EmailPostForm()

    return render(
        request,
        "blog/post/share.html",
        {"post": post, "form": form, "sent": sent},
    )
