import logging
import requests
import json
import os

import azure.functions as func



line_notify_access_token = os.environ["ACCESS_TOKEN"]

def getDailyChallengeTitle():
    """
    取得LeetCode Daily Challenge當日的題目標題
    """
    url = "https://leetcode.com/graphql/"
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"}
    query_json = {
        "query":"\n    query questionOfToday {\n  activeDailyCodingChallengeQuestion {\n    date\n    userStatus\n    link\n    question {\n      acRate\n      difficulty\n      freqBar\n      frontendQuestionId: questionFrontendId\n      isFavor\n      paidOnly: isPaidOnly\n      status\n      title\n      titleSlug\n      hasVideoSolution\n      hasSolution\n      topicTags {\n        name\n        id\n        slug\n      }\n    }\n  }\n}\n    ",
        "variables":{}
    }
    response = requests.post(url, json=query_json, headers=headers)
    titleInfo = json.loads(response.text)
    return titleInfo["data"]["activeDailyCodingChallengeQuestion"]["question"]["titleSlug"]


def getDailyChallengeInfo(title):
    """
    進入題目頁面抓取需要的資訊
    包含題號、題目名稱、難度、讚數、倒讚數、正確數、提交數、正確率、相關主題、題目連結網址
    """
    url = "https://leetcode.com/graphql/"
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"}
    query_json = {
        "operationName":"questionData",
        "query":"query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    exampleTestcases\n    categoryTitle\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      paidOnly\n      hasVideoSolution\n      paidOnlyVideo\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    enableTestMode\n    enableDebugger\n    envInfo\n    libraryUrl\n    adminUrl\n    challengeQuestion {\n      id\n      date\n      incompleteChallengeCount\n      streakCount\n      type\n      __typename\n    }\n    __typename\n  }\n}\n",
        "variables":{"titleSlug":title}
    }
    response = requests.post(url, json=query_json, headers=headers)
    question_info = json.loads(response.text)
    question_id = question_info["data"]["question"]["questionFrontendId"]
    question_title = question_info["data"]["question"]["title"]
    question_difficulty = question_info["data"]["question"]["difficulty"]
    likes_num = question_info["data"]["question"]["likes"]
    dislikes_num = question_info["data"]["question"]["dislikes"]
    stats = json.loads(question_info["data"]["question"]["stats"])
    question_accepted = stats["totalAcceptedRaw"]
    question_submissions = stats["totalSubmissionRaw"]
    question_acceptance = stats["acRate"]
    topics = question_info["data"]["question"]["topicTags"]
    question_topics = [topic["name"] for topic in topics]
    question_link = "https://leetcode.com/problems/{}/".format(title)
    return (question_id, question_title, question_difficulty, likes_num, dislikes_num, question_accepted, question_submissions, question_acceptance, question_topics, question_link)


def sendMessage(message):
    """
    利用line notify傳送訊息
    """
    headers = {
        "Authorization":f"Bearer {line_notify_access_token}"
    }
    payload = {
        "message":message
    }
    response = requests.post("https://notify-api.line.me/api/notify", data=payload, headers=headers)
    logging.info(response.text)


def main(mytimer: func.TimerRequest) -> None:
    try:
        title = getDailyChallengeTitle()
        infos = getDailyChallengeInfo(title)
        message = "\n{}.{}\n{}\nLikes:{:,}\nDislikes:{:,}\nAccepted:{:,}\nSubmissions:{:,}\nAcceptance:{}\nRelated Topics:\n{}\nLink:\n{}".format(*infos).replace("'", "")
        sendMessage(message)
    except Exception as e:
        message = f"\nThere are some problems.\nCkeck it out later.\nError Message:\n{e}"
        sendMessage(message)