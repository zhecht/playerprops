
import time
import nodriver as uc

async def main():
	url = "https://www.oh.bet365.com/#/AC/B12/C20426855/D47/E120593/F47/N7/"

	driver = await uc.start(no_sandbox=True)
	page = await driver.get(url)

	await page.wait_for(selector=".msl-ShowMoreLink")
	showMore = await page.query_selector_all(".msl-ShowMore_Link")

	await ShowMore[0].scroll_into_view()
	await showMore[0].mouse_click()

	time.sleep(20)

	driver.quit()

if __name__ == "__main__":
	uc.loop().run_until_complete(main())