import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_url(url, cookies):
    try:
        # 定义 Cookie 字符串
        cookie_str = '; '.join([f'{key}={value}' for key, value in reversed(cookies.items())])

        # 手动将 Cookie 添加到请求头
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": cookie_str,
            "Priority": "u=1, i",
            "Sec-Ch-Ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        }

        response = requests.get(url, headers=headers)
        return {'url': url, 'status_code': response.status_code, 'content': response.json()}
    except requests.RequestException as e:
        return {'url': url, 'error': str(e)}


# 多线程请求函数
def fetch_urls_concurrently(urls, cookies=None, max_workers=10):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有URL的请求
        future_to_url = {executor.submit(fetch_url, url, cookies): url for url in urls}

        # 逐个获取结果
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({'url': url, 'error': str(e)})

    return results
