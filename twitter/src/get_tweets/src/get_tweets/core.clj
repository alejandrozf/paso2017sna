(ns get-tweets.core
  ;;Siple I/O
  (:require [clojure.java.io :as io])
  ;; JSON library
  (:require [cheshire.core :refer :all])
  ;; MongoDB library
  (:require [monger.core :as mg])
  (:import [com.mongodb MongoOptions ServerAddress])
  ;; Twitter API
  (:use [twitter.oauth]
        [twitter.callbacks]
        [twitter.callbacks.handlers]
        [twitter.api.restful])
  (:import [twitter.callbacks.protocols AsyncSingleCallback])
  (:gen-class))

;; Mutable values, about connections state
(def active-credentials (agent {}))
(def current-index (agent 0))
(def active-pages (agent {}))

;; MongoDB connection
(def mongo-host "mongodb://localhost/paso2017_async")
(def mongo-port 27017)

;; Reading credentials
(def api-credentials (parse-stream (io/reader "credentials.json")))
(def len-credentials (count api-credentials))

(defn choose-oauth-credentials
  "Gives the credentials according 'index'"
  [index]
  (let [credential (nth api-credentials index)]
    (make-oauth-creds (get credential "consumer_key")
                      (get credential "consumer_secret")
                      (get credential "access_token")
                      (get credential "access_token_secret"))))

(defn switch-credential
  "Swith to another credential"
  []
  (send-off current-index (fn [x] (mod (inc x) len-credentials)))
  (when (false? (get @active-credentials @current-index false))
    (format "Switching to API Credentials #%d" @current-index)
    (send-off active-credentials assoc
              @current-index (choose-oauth-credentials @current-index))))

(defn get-timeline
  "Gets all tweets from user in range of dates"
  ([uid day]
   "pass1")
  ([uid from to]
   "pass2"))

;; (def user-id "845696348")
;; (def user-timeline (statuses-user-timeline :oauth-creds my-creds
;;                                            :params {:user-id user-id
;;                                                     :count 5}))

(defn -main
  "I don't do a whole lot ... yet."
  [& args]
  (println "Hello, World!"))
