# Copyright (C) 2024 - 2025 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.

from unittest.mock import Mock

import pytest
import requests
from pytest_loguru.plugin import caplog

from elabftw_usersync.elabftw import ElabFTW


def test_check_connection_returns_true_if_endpoint_responds_ok(requests_mock):
    mock_info = Mock()
    mock_info.status_code = 200
    mock_info.json.return_value = {
        "elabftw_version": "4.8.0",
        "elabftw_version_int": 50102,
        "ts_balance": 461,
        "all_users_count": 389,
        "active_users_count": 311,
        "items_count": 666,
        "teams_count": 18,
        "experiments_count": 10189,
        "experiments_timestamped_count": 1601,
        "uploads_filesize_sum": 25681672,
        "uploads_filesize_sum_formatted": "24.49 MiB",
    }
    mock_session = Mock()
    mock_session.get.side_effect = [
        mock_info,
    ]

    elabftw = ElabFTW("https://fake_host", "fake_key")
    elabftw.session = mock_session

    assert elabftw.check_connection() is True


def test_check_connection_raises_exception_if_connection_is_refused(
    caplog, requests_mock
):
    elabftw = ElabFTW("https://fake_host", "fake_key")

    requests_mock.get(
        f"{elabftw.host_url}/api/v2/info", exc=requests.exceptions.ConnectionError
    )

    with pytest.raises(SystemExit):
        elabftw.check_connection()
        assert "Error connecting to ElabFTW: Connection refused" in caplog.text


def test_check_connection_raises_exception_if_response_not_ok(caplog, requests_mock):
    elabftw = ElabFTW("https://fake_host", "fake_key")

    requests_mock.get(f"{elabftw.host_url}/api/v2/info", status_code=500)

    with pytest.raises(SystemExit):
        elabftw.check_connection()
        assert "Error connecting to ElabFTW: " in caplog.text


def test_get_users_for_team():
    mock_user_response1 = Mock()
    mock_user_response1.status_code = 200
    mock_user_response1.json.return_value = {
        "userid": 50,
        "usergroup_old": 4,
        "firstname": "Alice",
        "lastname": "Test",
        "email": "alice.test@uni-muenster.de",
        "orcid": None,
        "register_date": 1695028784,
        "limit_nb": 15,
        "sc_create": "c",
        "sc_edit": "e",
        "sc_favorite": "f",
        "sc_todo": "t",
        "show_team": 1,
        "show_team_templates": 0,
        "show_public": 0,
        "use_isodate": 0,
        "uploads_layout": 1,
        "validated": 1,
        "lang": "de_DE",
        "default_read": '{"base": 30, "teams": [], "users": [], "teamgroups": []}',
        "default_write": '{"base": 20, "teams": [], "users": [], "teamgroups": []}',
        "single_column_layout": 0,
        "cjk_fonts": 0,
        "orderby": "date",
        "sort": "desc",
        "use_markdown": 0,
        "inc_files_pdf": 1,
        "append_pdfs": 0,
        "pdf_format": "A4",
        "display_mode": "it",
        "last_login": None,
        "allow_untrusted": 1,
        "notif_comment_created": 1,
        "notif_comment_created_email": 1,
        "notif_user_created": 1,
        "notif_user_created_email": 1,
        "notif_user_need_validation": 1,
        "notif_user_need_validation_email": 1,
        "notif_step_deadline": 1,
        "notif_step_deadline_email": 1,
        "notif_event_deleted": 1,
        "notif_event_deleted_email": 1,
        "auth_lock_time": None,
        "auth_service": None,
        "pdf_sig": 0,
        "valid_until": None,
        "orgid": "muster_id",
        "is_sysadmin": 0,
        "sc_search": "s",
        "token_created_at": None,
        "entrypoint": 0,
        "disable_shortcuts": 0,
        "fullname": "Alice Test",
        "team": 1,
        "teams": [
            {
                "id": 1,
                "name": "Default team",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
            {
                "id": 58,
                "name": "ULB 2.2",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
        ],
    }

    mock_user_response2 = Mock()
    mock_user_response2.status_code = 200
    mock_user_response2.json.return_value = {
        "userid": 47,
        "usergroup_old": 4,
        "firstname": "Bob",
        "lastname": "Test",
        "email": "bob.test@uni-muenster.de",
        "orcid": None,
        "register_date": 1695028782,
        "limit_nb": 15,
        "sc_create": "c",
        "sc_edit": "e",
        "sc_favorite": "f",
        "sc_todo": "t",
        "show_team": 1,
        "show_team_templates": 0,
        "show_public": 0,
        "use_isodate": 0,
        "uploads_layout": 1,
        "validated": 1,
        "lang": "de_DE",
        "default_read": '{"base": 30, "teams": [], "users": [], "teamgroups": []}',
        "default_write": '{"base": 20, "teams": [], "users": [], "teamgroups": []}',
        "single_column_layout": 0,
        "cjk_fonts": 0,
        "orderby": "date",
        "sort": "desc",
        "use_markdown": 0,
        "inc_files_pdf": 1,
        "append_pdfs": 0,
        "pdf_format": "A4",
        "display_mode": "it",
        "last_login": None,
        "allow_untrusted": 1,
        "notif_comment_created": 1,
        "notif_comment_created_email": 1,
        "notif_user_created": 1,
        "notif_user_created_email": 1,
        "notif_user_need_validation": 1,
        "notif_user_need_validation_email": 1,
        "notif_step_deadline": 1,
        "notif_step_deadline_email": 1,
        "notif_event_deleted": 1,
        "notif_event_deleted_email": 1,
        "auth_lock_time": None,
        "auth_service": None,
        "pdf_sig": 0,
        "valid_until": None,
        "orgid": "muster_id",
        "is_sysadmin": 0,
        "sc_search": "s",
        "token_created_at": None,
        "entrypoint": 0,
        "disable_shortcuts": 0,
        "fullname": "Bob Test",
        "team": 1,
        "teams": [
            {
                "id": 1,
                "name": "Default team",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
            {
                "id": 4,
                "name": "Team B",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
            {
                "id": 58,
                "name": "ULB 2.2",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 1,
            },
        ],
    }

    mock_all_users_response = Mock()
    mock_all_users_response.status_code = 200
    mock_all_users_response.json.return_value = [
        {
            "userid": 50,
            "firstname": "Alice",
            "lastname": "Test",
            "orgid": "muster_id1",
            "email": "alice.test@uni-muenster.de",
            "validated": 1,
            "last_login": None,
            "valid_until": None,
            "is_sysadmin": 0,
            "fullname": "Alice Test",
            "orcid": None,
            "auth_service": None,
        },
        {
            "userid": 47,
            "firstname": "Bob",
            "lastname": "Test",
            "orgid": "muster_id",
            "email": "bob.test@uni-muenster.de",
            "validated": 1,
            "last_login": None,
            "valid_until": None,
            "is_sysadmin": 0,
            "fullname": "Bob Test",
            "orcid": None,
            "auth_service": None,
        },
    ]

    mock_session = Mock()
    mock_session.get.side_effect = [
        mock_all_users_response,
        mock_user_response1,
        mock_user_response2,
    ]

    elab = ElabFTW("https://example.com", "apikey")
    elab.session = mock_session
    elab.all_users = elab.get_all_users()
    elab.user_data_list = elab.create_users_dict()

    # Only get active users of the team, ignore archived ones
    assert elab.get_users_for_team(58) == [
        {"user_mail": "alice.test@uni-muenster.de", "user_id": 50, "orgid": "muster_id"}
    ]


def test_get_user_id():
    mock_user_response1 = Mock()
    mock_user_response1.status_code = 200
    mock_user_response1.json.return_value = {
        "userid": 50,
        "usergroup_old": 4,
        "firstname": "Alice",
        "lastname": "Test",
        "email": "alice.test@uni-muenster.de",
        "orcid": None,
        "register_date": 1695028784,
        "limit_nb": 15,
        "sc_create": "c",
        "sc_edit": "e",
        "sc_favorite": "f",
        "sc_todo": "t",
        "show_team": 1,
        "show_team_templates": 0,
        "show_public": 0,
        "use_isodate": 0,
        "uploads_layout": 1,
        "validated": 1,
        "lang": "de_DE",
        "default_read": '{"base": 30, "teams": [], "users": [], "teamgroups": []}',
        "default_write": '{"base": 20, "teams": [], "users": [], "teamgroups": []}',
        "single_column_layout": 0,
        "cjk_fonts": 0,
        "orderby": "date",
        "sort": "desc",
        "use_markdown": 0,
        "inc_files_pdf": 1,
        "append_pdfs": 0,
        "pdf_format": "A4",
        "display_mode": "it",
        "last_login": None,
        "allow_untrusted": 1,
        "notif_comment_created": 1,
        "notif_comment_created_email": 1,
        "notif_user_created": 1,
        "notif_user_created_email": 1,
        "notif_user_need_validation": 1,
        "notif_user_need_validation_email": 1,
        "notif_step_deadline": 1,
        "notif_step_deadline_email": 1,
        "notif_event_deleted": 1,
        "notif_event_deleted_email": 1,
        "auth_lock_time": None,
        "auth_service": None,
        "pdf_sig": 0,
        "valid_until": None,
        "orgid": "muster_id",
        "is_sysadmin": 0,
        "sc_search": "s",
        "token_created_at": None,
        "entrypoint": 0,
        "disable_shortcuts": 0,
        "fullname": "Alice Test",
        "team": 1,
        "teams": [
            {
                "id": 1,
                "name": "Default team",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
            {
                "id": 58,
                "name": "ULB 2.2",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
        ],
    }

    mock_user_response2 = Mock()
    mock_user_response2.status_code = 200
    mock_user_response2.json.return_value = {
        "userid": 47,
        "usergroup_old": 4,
        "firstname": "Bob",
        "lastname": "Test",
        "email": "bob.test@uni-muenster.de",
        "orcid": None,
        "register_date": 1695028782,
        "limit_nb": 15,
        "sc_create": "c",
        "sc_edit": "e",
        "sc_favorite": "f",
        "sc_todo": "t",
        "show_team": 1,
        "show_team_templates": 0,
        "show_public": 0,
        "use_isodate": 0,
        "uploads_layout": 1,
        "validated": 1,
        "lang": "de_DE",
        "default_read": '{"base": 30, "teams": [], "users": [], "teamgroups": []}',
        "default_write": '{"base": 20, "teams": [], "users": [], "teamgroups": []}',
        "single_column_layout": 0,
        "cjk_fonts": 0,
        "orderby": "date",
        "sort": "desc",
        "use_markdown": 0,
        "inc_files_pdf": 1,
        "append_pdfs": 0,
        "pdf_format": "A4",
        "display_mode": "it",
        "last_login": None,
        "allow_untrusted": 1,
        "notif_comment_created": 1,
        "notif_comment_created_email": 1,
        "notif_user_created": 1,
        "notif_user_created_email": 1,
        "notif_user_need_validation": 1,
        "notif_user_need_validation_email": 1,
        "notif_step_deadline": 1,
        "notif_step_deadline_email": 1,
        "notif_event_deleted": 1,
        "notif_event_deleted_email": 1,
        "auth_lock_time": None,
        "auth_service": None,
        "pdf_sig": 0,
        "valid_until": None,
        "orgid": "muster_id",
        "is_sysadmin": 0,
        "sc_search": "s",
        "token_created_at": None,
        "entrypoint": 0,
        "disable_shortcuts": 0,
        "fullname": "Bob Test",
        "team": 1,
        "teams": [
            {
                "id": 1,
                "name": "Default team",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
            {
                "id": 4,
                "name": "Team B",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
        ],
    }

    mock_all_users_response = Mock()
    mock_all_users_response.status_code = 200
    mock_all_users_response.json.return_value = [
        {
            "userid": 50,
            "firstname": "Alice",
            "lastname": "Test",
            "orgid": "muster_id1",
            "email": "alice.test@uni-muenster.de",
            "validated": 1,
            "last_login": None,
            "valid_until": None,
            "is_sysadmin": 0,
            "fullname": "Alice Test",
            "orcid": None,
            "auth_service": None,
        },
        {
            "userid": 47,
            "firstname": "Bob",
            "lastname": "Test",
            "orgid": "muster_id",
            "email": "bob.test@uni-muenster.de",
            "validated": 1,
            "last_login": None,
            "valid_until": None,
            "is_sysadmin": 0,
            "fullname": "Bob Test",
            "orcid": None,
            "auth_service": None,
        },
    ]

    mock_all_teams_response = Mock()
    mock_all_teams_response.status_code = 200
    mock_all_teams_response.json.return_value = [
        {
            "id": 1,
            "name": "Default team",
            "orgid": "default",
            "visible": 1,
        },
        {
            "id": 58,
            "name": "ULB 2.2",
            "orgid": "ulb22",
            "visible": 1,
        },
        {
            "id": 4,
            "name": "Team B",
            "orgid": "teamb",
            "visible": 1,
        },
        {
            "id": 2,
            "name": "Shadow Archive",
            "orgid": "userarchiv",
            "visible": 1,
        },
    ]

    mock_session = Mock()
    mock_session.get.side_effect = [
        mock_all_users_response,
        mock_user_response1,
        mock_user_response2,
        mock_all_teams_response,
    ]

    elab = ElabFTW("https://example.com", "apikey")
    elab.session = mock_session
    elab.all_users = elab.get_all_users()
    elab.user_data_list = elab.create_users_dict()

    assert elab.get_user_id("muster_id") == (47, False)


def test_unarchive_user_in_team_success():
    """Test successful unarchiving of a user in a team."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "userid": 47,
        "firstname": "Bob",
        "lastname": "Test",
        "email": "bob.test@uni-muenster.de",
        "teams": [
            {
                "id": 1,
                "name": "Default team",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,
            },
            {
                "id": 58,
                "name": "ULB 2.2",
                "usergroup": 4,
                "is_owner": 0,
                "is_archived": 0,  # Successfully unarchived
            },
        ],
    }

    mock_session = Mock()
    mock_session.patch.return_value = mock_response

    elab = ElabFTW("https://example.com", "apikey")
    elab.session = mock_session

    result = elab.unarchive_user_in_team(47, 58)

    # Verify the PATCH request was made with correct payload
    mock_session.patch.assert_called_once_with(
        "https://example.com/api/v2/users/47",
        json={
            "action": "patchuser2team",
            "userid": 47,
            "team": 58,
            "target": "is_archived",
            "content": False,
        },
    )

    # Verify the response is returned
    assert result == mock_response.json.return_value
    assert result["teams"][1]["is_archived"] == 0


def test_unarchive_user_in_team_with_tuple_user_id():
    """Test that tuple user_id is handled correctly."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "userid": 47,
        "teams": [
            {
                "id": 58,
                "name": "ULB 2.2",
                "is_archived": 0,
            },
        ],
    }

    mock_session = Mock()
    mock_session.patch.return_value = mock_response

    elab = ElabFTW("https://example.com", "apikey")
    elab.session = mock_session

    # Pass user_id as tuple
    result = elab.unarchive_user_in_team((47, False), 58)

    # Verify the PATCH request was made with extracted user_id
    mock_session.patch.assert_called_once_with(
        "https://example.com/api/v2/users/47",
        json={
            "action": "patchuser2team",
            "userid": 47,
            "team": 58,
            "target": "is_archived",
            "content": False,
        },
    )


def test_unarchive_user_in_team_error_handling(caplog):
    """Test error handling when unarchiving fails."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_session = Mock()
    mock_session.patch.return_value = mock_response

    elab = ElabFTW("https://example.com", "apikey")
    elab.session = mock_session

    result = elab.unarchive_user_in_team(47, 58)

    # Verify error was logged
    mock_session.patch.assert_called_once()
    assert result == mock_response.json.return_value
