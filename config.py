exit_flag = -1
get_booking_url = 'https://merchant.klook.com/v1/merchantapisrv/booking/booking_service/get_booking_list?merchant_category_id=0&activity_id=0&package_id=0&tag_id=-1&time_type=1&ticket_status=0&alter_status=0&pending_tag&booking_reference_number={}&lead_person_name&start_time={}&end_time={}&date[]={}&date[]={}&_isReset=true&_origin_merchant_id=0&page=1&limit=10&no_mask=false'

get_booking_list = 'https://merchant.klook.com/v1/merchantapisrv/booking/booking_service/get_booking_list?merchant_category_id=0&activity_id=0&package_id=0&tag_id=-1&time_type=1&ticket_status=4&alter_status=0&pending_tag=0&booking_reference_number&lead_person_name&start_time={}&end_time={}&date[]={}&date[]={}&_isReset=true&_origin_merchant_id=0&page={}&limit={}&no_mask=false'

get_car_list = 'https://merchant.klook.com/v1/privatetransfermerchantsrv/api/car/manager/list?pageNum={}&pageSize={}'

get_driver_list = 'https://merchant.klook.com/v1/privatetransfermerchantsrv/api/driver/manager/list?pageNum={}&pageSize={}'