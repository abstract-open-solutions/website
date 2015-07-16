# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Abstract srl (<http://www.abstract.it>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website_blog.controllers.main import WebsiteBlog, QueryURL


@http.route([
    '/blog',
    '/blog/page/<int:page>',
], type='http', auth="public", website=True)
def blogs(self, page=1, **post):
    cr, uid, context = request.cr, request.uid, request.context
    blog_obj = request.registry['blog.post']
    total = blog_obj.search(cr, uid, [], count=True, context=context)
    pager = request.website.pager(
        url='/blog',
        total=total,
        page=page,
        step=self._blog_post_per_page,
    )
    domain = [(
        'publication_date',
        '<=',
        datetime.strftime(datetime.today(), '%Y-%m-%d'))]
    post_ids = blog_obj.search(cr, uid, domain, offset=(page-1)*self._blog_post_per_page, limit=self._blog_post_per_page, context=context)
    posts = blog_obj.browse(cr, uid, post_ids, context=context)
    blog_url = QueryURL('', ['blog', 'tag'])
    return request.website.render("website_blog.latest_blogs", {
        'posts': posts,
        'pager': pager,
        'blog_url': blog_url,
    })

@http.route([
    '/blog/<model("blog.blog"):blog>',
    '/blog/<model("blog.blog"):blog>/page/<int:page>',
    '/blog/<model("blog.blog"):blog>/tag/<model("blog.tag"):tag>',
    '/blog/<model("blog.blog"):blog>/tag/<model("blog.tag"):tag>/page/<int:page>',
], type='http', auth="public", website=True)
def blog(self, blog=None, tag=None, page=1, **opt):
    """ Prepare all values to display the blog.

    :return dict values: values for the templates, containing

     - 'blog': current blog
     - 'blogs': all blogs for navigation
     - 'pager': pager of posts
     - 'tag': current tag
     - 'tags': all tags, for navigation
     - 'nav_list': a dict [year][month] for archives navigation
     - 'date': date_begin optional parameter, used in archives navigation
     - 'blog_url': help object to create URLs
    """
    date_begin, date_end = opt.get('date_begin'), opt.get('date_end')

    cr, uid, context = request.cr, request.uid, request.context
    blog_post_obj = request.registry['blog.post']

    blog_obj = request.registry['blog.blog']
    blog_ids = blog_obj.search(cr, uid, [], order="create_date asc", context=context)
    blogs = blog_obj.browse(cr, uid, blog_ids, context=context)

    domain = [(
        'publication_date', '<=',
        datetime.strftime(datetime.today(), '%Y-%m-%d'))]
    if blog:
        domain += [('blog_id', '=', blog.id)]
    if tag:
        domain += [('tag_ids', 'in', tag.id)]
    if date_begin and date_end:
        domain += [("create_date", ">=", date_begin), ("create_date", "<=", date_end)]

    blog_url = QueryURL('', ['blog', 'tag'], blog=blog, tag=tag, date_begin=date_begin, date_end=date_end)
    post_url = QueryURL('', ['blogpost'], tag_id=tag and tag.id or None, date_begin=date_begin, date_end=date_end)

    blog_post_ids = blog_post_obj.search(cr, uid, domain, order="publication_date desc", context=context)
    blog_posts = blog_post_obj.browse(cr, uid, blog_post_ids, context=context)

    pager = request.website.pager(
        url=blog_url(),
        total=len(blog_posts),
        page=page,
        step=self._blog_post_per_page,
    )
    pager_begin = (page - 1) * self._blog_post_per_page
    pager_end = page * self._blog_post_per_page
    blog_posts = blog_posts[pager_begin:pager_end]

    tags = blog.all_tags()[blog.id]

    values = {
        'blog': blog,
        'blogs': blogs,
        'tags': tags,
        'tag': tag,
        'blog_posts': blog_posts,
        'pager': pager,
        'nav_list': self.nav_list(),
        'blog_url': blog_url,
        'post_url': post_url,
        'date': date_begin,
    }
    response = request.website.render("website_blog.blog_post_short", values)
    return response

WebsiteBlog.blog = blog
WebsiteBlog.blogs = blogs
