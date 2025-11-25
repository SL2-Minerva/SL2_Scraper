
# import random
import json
import services.pantip_api as PantipService
import services.transaction as TransactionService


async def run():
    try:
        print("Pantip Api is started. ")

        # await scraping_data(keyword="การเมือง", paging=1)
        result = []
        data = await PantipService.get_post_and_comment_data_api(
            keyword="การเมือง",
            keyword_id=1,
            keyword_checks=["การเมือง"],
            keyword_excludes=[]
        )

        result.extend(data)

        await TransactionService.insert_post_and_comments_data_to_mysql(new_data=result)

        print("count", len(data))
    except Exception as e:
        print(f"Pantip\n\n run error\n{e}.")


async def scraping_data(keyword="", paging=1):
    data_result = []
    comment_result = []

    post_data = await PantipService.get_posts_data(
        keyword=keyword,
        paging=paging,
        keyword_checks=[keyword]
    )

    data_result.extend(post_data)

    for post in post_data:
        comments = await PantipService.get_comment_data_api(
            url=post["url"],
            keyword_checks=[keyword]
        )
        comment_result.extend(comments)

    print(json.dumps(data_result, indent=4, ensure_ascii=False))
    print("\n\n")
    print(json.dumps(comment_result, indent=4, ensure_ascii=False))
    print("\n\n")
    print("post count:", len(data_result))
    print("comment count:", len(comment_result))
