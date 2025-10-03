from django.db import models
from django.utils import timezone

from account.models import User
from utils.models import ModelMixin
from web.choices import *


# Create your models here.


class BlogCategory(ModelMixin):
    """Blog categories for organizing posts"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code for category')
    icon = models.CharField(max_length=50, blank=True, help_text='FontAwesome icon class')
    image = models.URLField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'blog_categories'
        verbose_name_plural = 'Blog Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.meta_title:
            self.meta_title = self.name
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    def get_all_posts(self):
        """Get all posts including from child categories"""
        categories = [self]
        categories.extend(self.children.all())
        return BlogPost.objects.active().filter(category__in=categories)


class BlogTag(ModelMixin):
    """Tags for blog posts"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text='Hex color code for tag')
    posts_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'blog_tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['posts_count']),
        ]

    def __str__(self):
        return self.name


class BlogPost(ModelMixin):
    """Main blog post model"""
    title = models.CharField(max_length=500)
    excerpt = models.TextField(max_length=300, blank=True, help_text='Short description for preview')
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPE, default='standard')
    post_status = models.CharField(max_length=20, choices=POST_STATUS, default='draft')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(BlogCategory, on_delete=models.PROTECT, related_name='posts')
    tags = models.ManyToManyField(BlogTag, blank=True, related_name='posts')
    featured_image = models.URLField(blank=True, null=True)
    featured_image_alt = models.CharField(max_length=255, blank=True)
    gallery_images = models.JSONField(default=list, blank=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Social Media
    og_title = models.CharField(max_length=255, blank=True, help_text='Open Graph title')
    og_description = models.TextField(max_length=300, blank=True, help_text='Open Graph description')
    og_image = models.URLField(blank=True, null=True, help_text='Open Graph image')

    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    # Settings
    allow_comments = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'blog_posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', 'post_status']),
            models.Index(fields=['category', 'post_status']),
            models.Index(fields=['is_featured', 'post_status']),
            models.Index(fields=['post_status']),
            models.Index(fields=['views_count']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):

        # Auto-generate SEO fields
        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]

        # Set published_at when status changes to published
        # if self.post_status == 'published' and not self.published_at:
        #     self.published_at = timezone.now()

        # Calculate reading time
        # if self.content:
        #     word_count = len(self.content.split())
        #     self.estimated_read_time = max(1, round(word_count / 200))  # 200 words per minute

        super().save(*args, **kwargs)

    @property
    def is_published(self):
        """Check if post is published"""
        return (
                self.post_status == 'published'
        )

    # @property
    # def reading_time_text(self):
    #     """Get reading time as text"""
    #     if self.estimated_read_time == 1:
    #         return "1 minute read"
    #     return f"{self.estimated_read_time} minutes read"

    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def get_related_posts(self, limit=5):
        """Get related posts based on category and tags"""
        related = BlogPost.objects.active().filter(
            post_status='published'
        ).exclude(id=self.id)

        # Posts in same category
        same_category = related.filter(category=self.category)[:limit]

        if same_category.count() >= limit:
            return same_category

        # Fill with posts having similar tags
        remaining = limit - same_category.count()
        similar_tags = related.filter(
            tags__in=self.tags.all()
        ).exclude(
            id__in=same_category.values_list('id', flat=True)
        ).distinct()[:remaining]

        return list(same_category) + list(similar_tags)


class BlogComment(ModelMixin):
    """Comments on blog posts"""
    # Comment Details
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    # User Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='blog_comments')
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)
    guest_phone_number = models.CharField(max_length=15, blank=True)

    # Comment Content
    content = models.TextField(max_length=1000)
    comment_status = models.CharField(max_length=20, choices=COMMENT_STATUS, default='pending')

    # Engagement
    likes_count = models.PositiveIntegerField(default=0)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Moderation
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'blog_comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'comment_status']),
            models.Index(fields=['user', 'comment_status']),
            models.Index(fields=['parent']),
            models.Index(fields=['comment_status', 'created_at']),
        ]

    def __str__(self):
        author = self.user.get_full_name() if self.user else self.guest_name
        return f"Comment by {author} on {self.post.title}"

    @property
    def author_name(self):
        """Get comment author name"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name

    @property
    def author_email(self):
        """Get comment author email"""
        if self.user:
            return self.user.email
        return self.guest_email

    def get_replies(self):
        """Get approved replies to this comment"""
        return self.replies.filter(comment_status='approved').order_by('created_at')

    def approve(self):
        """Approve comment"""
        self.comment_status = 'approved'
        self.save(update_fields=['comment_status'])

        # Update post comment count
        self.post.comments_count = self.post.comments.filter(comment_status='approved').count()
        self.post.save(update_fields=['comments_count'])


class BlogPostView(ModelMixin):
    """Track individual post views for analytics"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='post_views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    time_spent = models.IntegerField(default=0, help_text='Time spent reading in seconds')
    scroll_percentage = models.IntegerField(default=0, help_text='Percentage of page scrolled')

    class Meta:
        db_table = 'blog_post_views'
        indexes = [
            models.Index(fields=['post', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['ip_address', 'viewed_at']),
        ]

